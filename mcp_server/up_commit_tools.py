from typing import Any, Dict, Optional, Sequence
import re

from .audit_logger import log_tool_call
from .database import Database
from .time_filter import get_time_range

ORG_ALLOWED = 2133
DEFAULT_LIMIT = 50


def _success(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"success": True, "data": payload}


def _error(message: str) -> Dict[str, Any]:
    return {"success": False, "error": str(message)}


def _norm_params(params: Optional[Sequence]) -> tuple:
    if params is None:
        return ()
    if isinstance(params, (list, tuple)):
        return tuple(params)
    return (params,)


def get_table_schema(table_name: str) -> Dict:
    log_tool_call("commit.get_table_schema", table=table_name)
    sql = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'insightly' AND table_name = %s
    ORDER BY ordinal_position
    """
    db = Database()
    try:
        res = db.execute_query(sql, params=(table_name,))
        if not res["success"]:
            return _error(res.get("error"))
        return _success({"columns": res["rows"]})
    finally:
        db.close()


def get_commit_summary(commit_id: int) -> Dict:
    log_tool_call("commit.get_commit_summary", commit_id=commit_id)
    sql = """
    SELECT
        id,
        commitid,
        authorid,
        message,
        repoid,
        branch,
        date,
        linesadded,
        linesremoved,
        htmllink,
        type
    FROM insightly.commit
    WHERE organizationid = %s AND id = %s
    LIMIT 1
    """
    db = Database()
    try:
        res = db.execute_query(sql, params=(ORG_ALLOWED, commit_id))
        if not res["success"]:
            return _error(res.get("error", "query failed"))
        if not res["rows"]:
            return _error("Commit not found")
        return _success({"commit": res["rows"][0]})
    finally:
        db.close()


def get_commit_count_period(period: str) -> Dict:
    log_tool_call("commit.get_commit_count_period", period=period)
    start_dt, end_dt = get_time_range(period)
    sql = """
    SELECT COUNT(*) AS commit_count
    FROM insightly.commit
    WHERE organizationid = %s
      AND date BETWEEN %s AND %s
    """
    db = Database()
    try:
        res = db.execute_query(
            sql, params=(ORG_ALLOWED, start_dt.isoformat(), end_dt.isoformat())
        )
        if not res["success"]:
            return _error(res.get("error"))
        count = res["rows"][0].get("commit_count", 0) if res["rows"] else 0
        return _success(
            {
                "period": period,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "commit_count": int(count),
            }
        )
    finally:
        db.close()


def get_commits_period(
    period: str, offset: int = 0, limit: Optional[int] = None
) -> Dict:
    log_tool_call("commit.get_commits_period", period=period, offset=offset, limit=limit)
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
            if limit_val <= 0 or limit_val > 100:
                return _error("limit must be between 1 and 100")
        except Exception:
            return _error("limit must be an integer")

    start_dt, end_dt = get_time_range(period)

    count_sql = """
    SELECT COUNT(*) AS commit_count
    FROM insightly.commit
    WHERE organizationid = %s
      AND date BETWEEN %s AND %s
    """
    list_sql = """
    SELECT
        id,
        commitid,
        authorid,
        message,
        date,
        repoid,
        branch,
        linesadded,
        linesremoved
    FROM insightly.commit
    WHERE organizationid = %s
      AND date BETWEEN %s AND %s
    ORDER BY date DESC
    LIMIT %s OFFSET %s
    """

    db = Database()
    try:
        count_res = db.execute_query(
            count_sql, params=(ORG_ALLOWED, start_dt.isoformat(), end_dt.isoformat())
        )
        if not count_res["success"]:
            return _error(count_res.get("error"))
        total = count_res["rows"][0].get("commit_count", 0) if count_res["rows"] else 0

        list_res = db.execute_query(
            list_sql,
            params=(
                ORG_ALLOWED,
                start_dt.isoformat(),
                end_dt.isoformat(),
                limit_val,
                offset_val,
            ),
        )
        if not list_res["success"]:
            return _error(list_res.get("error"))

        return _success(
            {
                "period": period,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "offset": offset_val,
                "limit": limit_val,
                "commit_count": int(total),
                "commits": list_res.get("rows", []),
            }
        )
    finally:
        db.close()


def _is_read_only_select(sql: str) -> bool:
    s = sql.strip().lower()
    s = re.sub(r"^\(+", "", s).strip()
    if not s.startswith("select"):
        return False
    forbidden = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        ";",
        "grant",
        "revoke",
        "call",
        "merge",
    ]
    for kw in forbidden:
        if kw in s:
            return False
    return True


def _has_limit_clause(sql: str) -> bool:
    return bool(re.search(r"\blimit\b", sql, flags=re.IGNORECASE))


def _contains_org_filter(sql: str) -> bool:
    return "organizationid" in sql.lower()


def _wrap_with_org_and_limit(sql: str, params: tuple, limit: int = DEFAULT_LIMIT):
    wrapped_sql = f"SELECT * FROM ({sql}) AS sub WHERE sub.organizationid = %s LIMIT %s"
    wrapped_params = tuple(params) + (ORG_ALLOWED, limit)
    return wrapped_sql, wrapped_params


def run_custom_commit_query(
    sql: str, params: Optional[Sequence] = None, limit: Optional[int] = None
) -> Dict:
    log_tool_call("commit.run_custom_commit_query")
    if not isinstance(sql, str) or not sql.strip():
        return _error("Invalid SQL provided")
    if ";" in sql.strip().rstrip().rstrip(";"):
        return _error("Multiple SQL statements are not allowed")
    if not _is_read_only_select(sql):
        return _error("Only read-only SELECT queries are allowed")

    params_t = _norm_params(params)
    user_limit = DEFAULT_LIMIT
    if limit is not None:
        try:
            user_limit = int(limit)
            if user_limit <= 0 or user_limit > 500:
                return _error("limit must be between 1 and 500")
        except Exception:
            return _error("invalid limit value")

    db = Database()
    try:
        if _contains_org_filter(sql):
            if not _has_limit_clause(sql):
                wrapped_sql = f"SELECT * FROM ({sql}) AS sub LIMIT %s"
                wrapped_params = tuple(params_t) + (user_limit,)
                res = db.execute_query(wrapped_sql, params=wrapped_params)
            else:
                res = db.execute_query(sql, params=params_t)
        else:
            wrapped_sql, wrapped_params = _wrap_with_org_and_limit(
                sql, params_t, user_limit
            )
            res = db.execute_query(wrapped_sql, params=wrapped_params)

        if not res["success"]:
            return _error("Query execution failed (internal error).")
        rows = res.get("rows", [])
        return _success({"rows": rows, "rowcount": len(rows)})
    finally:
        db.close()
