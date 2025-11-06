from mcp.server.fastmcp import FastMCP
from mcp_server import up_pr_tools as pr_tools


mcp = FastMCP("PR Analytics MCP Server")


@mcp.tool()
def list_tables() -> dict:
    """List available Insightly tables (internal use only)."""
    return pr_tools.list_tables()


@mcp.tool()
def get_pr_table_schema(table_name: str) -> dict:
    """Return column metadata for a given table name."""
    return pr_tools.get_table_schema(table_name)


@mcp.tool()
def get_pr_summary(pr_id: int) -> dict:
    """Fetch the full pull request record for the given PR id."""
    return pr_tools.get_pr_summary(pr_id)


@mcp.tool()
def get_review_time(pr_id: int) -> dict:
    """Return review time metrics (in minutes) for a PR."""
    return pr_tools.get_review_time(pr_id)


@mcp.tool()
def get_cycle_time(pr_id: int) -> dict:
    """Return cycle time metrics (in minutes) for a PR."""
    return pr_tools.get_cycle_time(pr_id)


@mcp.tool()
def get_pr_count_period(period: str) -> dict:
    """Count PRs within a natural language period (e.g., 'last 5 days')."""
    return pr_tools.get_pr_count_period(period)


@mcp.tool()
def get_prs_by_period(
    period: str,
    offset: int = 0,
    limit: int | None = None,
    min_cycle_time_minutes: float | None = None,
) -> dict:
    """List PRs in a period with optional cycle-time filter."""
    return pr_tools.get_prs_by_period(
        period,
        offset=offset,
        limit=limit,
        min_cycle_time_minutes=min_cycle_time_minutes,
    )


@mcp.tool()
def get_churn_metrics(pr_id: int) -> dict:
    """Compute churn metrics (lines added/removed, density, etc.) for a PR."""
    return pr_tools.get_churn_metrics(pr_id)


@mcp.tool()
def run_custom_pr_query(sql: str, params: list | None = None, limit: int | None = None) -> dict:
    """Execute a safeguarded read-only PR query with enforced org scope and limits."""
    return pr_tools.run_custom_pr_query(sql, params=params, limit=limit)


@mcp.tool()
def safe_sql(sql: str, params: list | None = None, limit: int | None = None) -> dict:
    """Alias for run_custom_pr_query."""
    return pr_tools.run_custom_pr_query(sql, params=params, limit=limit)


if __name__ == "__main__":
    print("Updated PR MCP Server starting...")
    mcp.run(transport="stdio")
