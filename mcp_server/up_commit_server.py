from mcp.server.fastmcp import FastMCP

from mcp_server import up_commit_tools as commit_tools

mcp = FastMCP("Commit Analytics MCP Server")


@mcp.tool()
def get_table_schema(table_name: str) -> dict:
    return commit_tools.get_table_schema(table_name)


@mcp.tool()
def get_commit_summary(commit_id: int) -> dict:
    return commit_tools.get_commit_summary(commit_id)


@mcp.tool()
def get_commit_count_period(period: str) -> dict:
    return commit_tools.get_commit_count_period(period)


@mcp.tool()
def get_commits_period(period: str, offset: int = 0, limit: int | None = None) -> dict:
    return commit_tools.get_commits_period(period, offset, limit)


@mcp.tool()
def run_custom_commit_query(
    sql: str, params: list | None = None, limit: int | None = None
) -> dict:
    return commit_tools.run_custom_commit_query(sql, params, limit)


if __name__ == "__main__":
    print("Updated Commit MCP Server starting...")
    mcp.run(transport="stdio")
