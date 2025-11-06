# `up_commit_agent` Startup Failure

## Summary

Running `uv run up_commit_agent.py` currently fails with `mcp.shared.exceptions.McpError: Connection closed`.  
The failure occurs before the agent can connect to its MCP server; the server process aborts immediately because it imports a module that does not exist in the package.

## Reproduction

```powershell
(.venv) D:\AI-Week\pr_risk_agent\mcp_server> uv run up_commit_agent.py
Error initializing MCP server: Connection closed
Traceback (most recent call last):
  ...
  File "…\agents\mcp\server.py", line 283, in connect
    server_result = await session.initialize()
  ...
  File "…\agents\mcp\shared\session.py", line 286, in send_request
    raise McpError(response_or_error.error)
mcp.shared.exceptions.McpError: Connection closed
```

Running the MCP server module directly shows the underlying exception:

```powershell
(.venv) D:\AI-Week\pr_risk_agent> uv run -m mcp_server.up_commit_server
Traceback (most recent call last):
  File "…\mcp_server\up_commit_server.py", line 2, in <module>
    from mcp_server import commit_tools
ImportError: cannot import name 'commit_tools' from 'mcp_server'
```

## Root Cause

`mcp_server/up_commit_server.py` still imports `commit_tools` from the package:

```python
from mcp_server import commit_tools
```

But the package no longer contains a `commit_tools.py` module—only the legacy version in `old server/commit_tools.py` and the empty stub `mcp_server/up_commit_tools.py`. Because the import fails, the server process terminates before responding to the client's `initialize` request, which the client surfaces as “Connection closed.”

## How to Fix

You need a working commit MCP tool module inside `mcp_server`. Choose one of the following approaches:

1. **Point the server at the new module**
   - Implement the desired tools in `mcp_server/up_commit_tools.py`.
   - Update `up_commit_server.py` to import that module:
     ```python
     from mcp_server import up_commit_tools as commit_tools
     ```
   - Ensure the functions referenced (`get_table_schema`, `get_commit_summary`, `get_commits_period`, `run_custom_commit_query`) exist in the module.

2. **Restore the legacy module**
   - Copy or move `old server/commit_tools.py` into `mcp_server/commit_tools.py`.
   - Adjust its API so it matches what `up_commit_server.py` expects.
   - Remove the empty `up_commit_tools.py` if it is no longer needed.

After either fix:

```powershell
(.venv) D:\AI-Week\pr_risk_agent> uv run -m mcp_server.up_commit_server
# should print “Updated Commit MCP Server starting…” and stay running

(.venv) D:\AI-Week\pr_risk_agent\mcp_server> uv run up_commit_agent.py
# agent should now produce a commit summary instead of crashing
```

## Next Steps Checklist

- [ ] Decide whether to build a new `up_commit_tools` implementation or reuse the legacy `commit_tools`.
- [ ] Ensure every tool referenced in `up_commit_server.py` exists and returns the expected structure.
- [ ] Re-run `uv run -m mcp_server.up_commit_server` to verify the server starts cleanly.
- [ ] Re-run `uv run up_commit_agent.py` and confirm the agent reaches a final response.
