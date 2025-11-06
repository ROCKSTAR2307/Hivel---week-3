from mcp.server.fastmcp import FastMCP

from mcp_server import up_commit_tools as commit_tools

mcp = FastMCP("Commit Analytics MCP Server")


@mcp.tool()
def get_table_schema(table_name: str) -> dict:
    """Get the schema of the table with table name"""
    return commit_tools.get_table_schema(table_name)


@mcp.tool()
def get_commit_summary(commit_id: int) -> dict:
    """Get the summary about the given commit made with the given commit id """
    return commit_tools.get_commit_summary(commit_id)


@mcp.tool()
def get_commit_count_period(period: str) -> dict:
    """Get the count of commit for a given period of time either in terms of n days or 
    weeks or months 
    """
    return commit_tools.get_commit_count_period(period)


@mcp.tool()
def get_commits_period(period: str, offset: int = 0, limit: int | None = None) -> dict:
    """Get the details of the commits for a given period of time either in terms of n days or
    weeks or months 
    """
    return commit_tools.get_commits_period(period, offset, limit)


@mcp.tool()
def run_custom_commit_query(
    
    sql: str, params: list | None = None, limit: int | None = None
) -> dict:
    """Execute a safeguarded read-only PR query with enforced org scope and limits. Get the 
    required data through existing tools, and only use this if you need to do something that is not supported by other tools.
    The SQL must be written in PostgreSQL syntax.
    """
    return commit_tools.run_custom_commit_query(sql, params, limit)


if __name__ == "__main__":
    print("Updated Commit MCP Server starting...")
    mcp.run(transport="stdio")
