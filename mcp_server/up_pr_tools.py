# pr_tools.py
from typing import Any, Dict, Optional, Sequence
import re

from .audit_logger import log_tool_call
from .database import Database
from .time_filter import get_time_range

def _success(payload):
    return {"success": True, "data": payload}

def _error(msg):
    return {"success": False, "error": str(msg)}

# Helper to normalize params used in Database.execute_query
def _norm_params(params: Optional[Sequence]):
    if params is None:
        return ()
    if isinstance(params, (list, tuple)):
        return tuple(params)
    return (params,)

# 1) list_tables - returns table names (internal use)
def list_tables() -> Dict:
    log_tool_call("pr.list_tables")
    sql = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'insightly'
    """
    db = Database()
    res = db.execute_query(sql, params=())
    if not res["success"]:
        return _error(res.get("error"))
    tables = [r.get("table_name") for r in res["rows"]]
    db.close() 
    return _success({"tables": tables})
    

# 2) get_table_schema(table_name) - returns column names/types
def get_pr_table_schema(table_name: str) -> Dict:
    """This tool has the whole table column information. This is the schema of the table."""
    log_tool_call("pr.get_table_schema", table=table_name)
    sql = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'insightly' AND table_name = %s
    ORDER BY ordinal_position
    """
    db = Database()
    res = db.execute_query(sql, params=(table_name,))
    if not res["success"]:
        return _error(res.get("error"))
    db.close() 
    return _success({"columns": res["rows"]})

# 3) get_pr_count_period(period) - returns count for organizationid=2133
def get_pr_count_period(period: str) -> Dict:
    log_tool_call("pr.get_pr_count_period", period=period)
    start_dt, end_dt = get_time_range(period)
    start = start_dt.isoformat()
    end = end_dt.isoformat()
    sql = """
    SELECT COUNT(*) AS pr_count
    FROM insightly.pull_request
    WHERE organizationid = 2133 AND createdon BETWEEN %s AND %s
    """
    db = Database()
    res = db.execute_query(sql, params=(start, end))
    if not res["success"]:
        return _error(res.get("error"))
    count = res["rows"][0].get("pr_count", 0) if res["rows"] else 0
    db.close() 
    return _success({"period": period, "start": start, "end": end, "pr_count": int(count)})


def get_prs_by_period(
    period: str,
    offset: int = 0,
    limit: Optional[int] = None,
    min_cycle_time_minutes: Optional[float] = None,
) -> Dict:
    """
    Return paginated PR metadata for a period, optionally filtering by cycle time.
    """
    log_tool_call(
        "pr.get_prs_by_period",
        period=period,
        offset=offset,
        limit=limit,
        min_cycle_time=min_cycle_time_minutes,
    )

    try:
        offset_val = int(offset)
        if offset_val < 0:
            return _error("offset must be non-negative")
    except Exception:
        return _error("offset must be an integer")

    if limit is None:
        limit_val = DEFAULT_LIMIT
    else:
        try:
            limit_val = int(limit)
            if limit_val <= 0 or limit_val > 50:
                return _error("limit must be between 1 and 50")
        except Exception:
            return _error("limit must be an integer")

    start_dt, end_dt = get_time_range(period)
    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()

    count_sql = """
    SELECT COUNT(*) AS pr_count
    FROM insightly.pull_request
    WHERE organizationid = %s
      AND createdon BETWEEN %s AND %s
    """
    list_sql = """
    SELECT
        actualpullrequestid,
        title,
        state,
        authorid,
        createdon,
        mergedon,
        cycletimeduration,
        opentoreviewduration,
        committoopenduration,
        linesadded,
        linesremoved,
        modifiedfilescount
    FROM insightly.pull_request
    WHERE organizationid = %s
      AND createdon BETWEEN %s AND %s
    """

    params_base: list[Any] = [ORG_ALLOWED, start_iso, end_iso]
    if min_cycle_time_minutes is not None:
        count_sql += "      AND cycletimeduration >= %s\n"
        list_sql += "      AND cycletimeduration >= %s\n"
        params_base.append(min_cycle_time_minutes)

    list_sql += "    ORDER BY createdon DESC\n    LIMIT %s OFFSET %s\n"

    db = Database()
    try:
        count_res = db.execute_query(count_sql, params=tuple(params_base))
        if not count_res["success"]:
            return _error(count_res.get("error"))
        total = count_res["rows"][0].get("pr_count", 0) if count_res["rows"] else 0

        list_params = tuple(params_base + [limit_val, offset_val])
        list_res = db.execute_query(list_sql, params=list_params)
        if not list_res["success"]:
            return _error(list_res.get("error"))

        return _success(
            {
                "period": period,
                "start": start_iso,
                "end": end_iso,
                "offset": offset_val,
                "limit": limit_val,
                "pr_count": int(total),
                "prs": list_res.get("rows", []),
            }
        )
    finally:
        db.close()

# 4) get_cycle_time(pr_id) - single-value metric (minutes)
def get_cycle_time(pr_id: int) -> Dict:
    log_tool_call("pr.get_cycle_time", pr_id=pr_id)
    sql = """
    SELECT cycletimeduration AS cycle_time_minutes
    FROM insightly.pull_request
    WHERE organizationid = 2133 AND actualpullrequestid = %s
    LIMIT 1
    """
    db = Database()
    res = db.execute_query(sql, params=(pr_id,))
    if not res["success"]:
        return _error(res.get("error"))
    if not res["rows"]:
        return _error("PR not found")
    val = res["rows"][0].get("cycle_time_minutes")
    db.close()
    return _success(
        {"cycle_time_minutes": float(val) if val is not None else None}
    )

# 5) get_review_time(pr_id) - example metric (minutes)
def get_review_time(pr_id: int) -> Dict:
    log_tool_call("pr.get_review_time", pr_id=pr_id)
    sql = """
    SELECT opentoreviewduration AS review_time_minutes
    FROM insightly.pull_request
    WHERE organizationid = 2133 AND actualpullrequestid = %s
    LIMIT 1
    """
    db = Database()
    try:
        res = db.execute_query(sql, params=(pr_id,))
        if not res["success"]:
            return _error(res.get("error"))
        if not res["rows"]:
            return _error("PR not found")
        val = res["rows"][0].get("review_time_minutes")
        return _success(
            {"review_time_minutes": float(val) if val is not None else None}
        )
    finally:
        db.close()

# 6) get_pr_summary(pr_id) - aggregate many bits into a single dict
def get_pr_summary(pr_id: int) -> Dict:
    """
    Fetches all available info about a given PR from the database.
    Express all the details in 5-10 lines about the PR.
    This function should be called after validating input, so no need to check for errors.
    This tool has access to all the columns in the pull_request table.
    """
    log_tool_call("pr.get_pr_summary", pr_id=pr_id)
    db = Database()
    sql = """
    SELECT *
    FROM insightly.pull_request
    WHERE organizationid = 2133 AND actualpullrequestid = %s
    LIMIT 1
    """
    res = db.execute_query(sql, params=(pr_id,))
    if not res["success"]:
        return _error(res.get("error", "Query failed"))
    if not res["rows"]:
        return _error("PR not found")
    db.close() 
    return _success({"pr_data": res["rows"][0]})

def get_churn_metrics(pr_id: int) -> Dict:
    """
    Compute churn metrics for the given PR id.
    Returns:
      - churn_lines: linesadded + linesremoved
      - churn_per_file: churn_lines / modifiedfilescount (if modifiedfilescount > 0)
      - commits_count: if available as commitscount column
    """
    log_tool_call("pr.get_churn_metrics", pr_id=pr_id)
    sql = """
    SELECT linesadded, linesremoved, modifiedfilescount, commitscount
    FROM insightly.pull_request
    WHERE organizationid = 2133 AND actualpullrequestid = %s
    LIMIT 1
    """
    db = Database()
    try:
        res = db.execute_query(sql, params=(pr_id,))
        if not res["success"]:
            return _error(res.get("error", "query failed"))

        if not res["rows"]:
            return _error("PR not found")

        row = res["rows"][0]
        linesadded = row.get("linesadded")
        linesremoved = row.get("linesremoved")
        files_changed = row.get("modifiedfilescount")
        commits_count = row.get("commitscount")

        churn_lines = None
        if linesadded is not None or linesremoved is not None:
            churn_lines = float((linesadded or 0) + (linesremoved or 0))
            churn_lines = round(churn_lines, 2)

        churn_per_file = None
        if churn_lines is not None and files_changed and files_changed > 0:
            churn_per_file = round(churn_lines / float(files_changed), 2)

        result = {"churn_lines": churn_lines, "churn_per_file": churn_per_file}
        if files_changed is not None:
            try:
                result["files_changed"] = int(files_changed)
            except Exception:
                result["files_changed"] = files_changed
        if commits_count is not None:
            try:
                result["commits_count"] = int(commits_count)
            except Exception:
                result["commits_count"] = commits_count

        return _success(result)
    finally:
        db.close()



ORG_ALLOWED = 2133
DEFAULT_LIMIT = 10



def _is_read_only_select(sql: str) -> bool:
    """Quick heuristic: must start with SELECT and not contain forbidden keywords or semicolons."""
    s = sql.strip().lower()
    # remove leading parentheses and whitespace
    s = re.sub(r'^\(+', '', s).strip()
    if not s.startswith("select"):
        return False
    forbidden = ["insert", "update", "delete", "drop", "alter", "truncate", "create", "grant", "revoke"]
    for kw in forbidden:
        if kw in s:
            return False
    return True

def _has_limit_clause(sql: str) -> bool:
    """Simple check for LIMIT presence - not perfect but reasonable."""
    return bool(re.search(r"\blimit\b", sql, flags=re.IGNORECASE))

def _contains_org_filter(sql: str) -> bool:
    return "organizationid" in sql.lower()

def _wrap_with_org_and_limit(sql: str, params: tuple, limit: int = DEFAULT_LIMIT):
    """
    Wraps the provided SQL as an inner query and applies an outer WHERE for organizationid
    and a LIMIT. Returns (wrapped_sql, wrapped_params)
    NOTE: This requires the inner query to project an `organizationid` column.
    """
    wrapped_sql = f"SELECT * FROM ({sql}) AS sub WHERE sub.organizationid = %s LIMIT %s"
    wrapped_params = tuple(params) + (ORG_ALLOWED, limit)
    return wrapped_sql, wrapped_params

def _norm_params(params: Optional[Sequence]):
    if params is None:
        return ()
    if isinstance(params, (list, tuple)):
        return tuple(params)
    return (params,)

def run_custom_pr_query(sql: str, params: Optional[Sequence] = None, limit: Optional[int] = None) -> Dict:
    """
    Execute a read-only, parameterized SQL query with enforcement:
      - Query must be a SELECT and read-only.
      - organizationid = 2133 must be present either in SQL or be present in the inner result (see wrap).
      - Enforces a LIMIT when necessary.
    Returns: {"success": True, "data": {"rows": [...], "rowcount": N}} or error dict.
    """
    try:
        if not isinstance(sql, str) or not sql.strip():
            return _error("Invalid SQL provided")

        # basic sanitation checks
        if not _is_read_only_select(sql):
            return _error("Only read-only SELECT queries are allowed")

        # normalize params
        params_t = _norm_params(params)

        # ensure no multiple statements / semicolons
        if ";" in sql.strip().rstrip().rstrip(";"):
            return _error("Multiple SQL statements are not allowed")

        # decide on limit
        user_limit = None
        if limit is not None:
            try:
                user_limit = int(limit)
                if user_limit <= 0:
                    return _error("limit must be a positive integer")
            except Exception:
                return _error("invalid limit value")

        db = Database()

        # If SQL already contains a reference to organizationid, allow execution but still enforce an upper bound on rows.
        if _contains_org_filter(sql):
            # If SQL has no LIMIT, enforce one by wrapping the query in an outer select with LIMIT.
            if not _has_limit_clause(sql):
                enforced_limit = user_limit or DEFAULT_LIMIT
                wrapped_sql = f"SELECT * FROM ({sql}) AS sub LIMIT %s"
                wrapped_params = tuple(params_t) + (enforced_limit,)
                res = db.execute_query(wrapped_sql, params=wrapped_params)
            else:
                # SQL includes org filter and includes a limit — we still ensure an upper cap by refusing huge user limits may be tricky;
                # rely on DB or caller to limit. Here we just execute with normalized params.
                res = db.execute_query(sql, params=params_t)
        else:
            # SQL does NOT reference organizationid -> we will only allow it if the inner query returns organizationid column.
            # To be safe we wrap the query and apply outer filter on sub.organizationid
            # NOTE: This requires the inner query to include an organizationid column.
            # If that's not true, the DB will error and we will return an error (we do not try to infer).
            enforced_limit = user_limit or DEFAULT_LIMIT
            wrapped_sql, wrapped_params = _wrap_with_org_and_limit(sql, params_t, enforced_limit)
            res = db.execute_query(wrapped_sql, params=wrapped_params)
        db.close() 
        if not res["success"]:
            # don't reveal DB errors directly; return a sanitized message
            return _error("Query execution failed (internal error).")

        rows = res.get("rows", [])
        return _success({"rows": rows, "rowcount": len(rows)})
    except Exception as e:
        # log internally, return safe message
        # logger.exception("run_custom_pr_query failed", exc_info=e)
        return _error("An unexpected error occurred while executing the query")
