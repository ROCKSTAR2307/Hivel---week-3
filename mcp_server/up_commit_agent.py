from pathlib import Path
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import sys
import asyncio
from commit_message import COMMIT_BOT_MESSAGE
from audit_logger import log_agent_start, log_user_query

async def run():
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    
    async with MCPServerStdio(
        params={
            "command": sys.executable,
            "args": ["-m", "mcp_server.up_commit_server"],
            "cwd": str(project_root),
        },
    ) as server:
        log_agent_start("commit_agent")
        agent = Agent(
            name="commit_agent",
            model="gpt-4.1-mini",
            instructions=COMMIT_BOT_MESSAGE,
            mcp_servers=[server],
        )
        
        prompt = "Count of commits MADE LAST 5 DAYS"
        log_user_query("commit_agent", prompt)
        result = await Runner.run(agent, prompt)
        print(result.final_output)

def main():
    base_dir = Path(__file__).resolve().parent
    load_dotenv(base_dir / ".env")
    load_dotenv(base_dir.parent / ".env")
    asyncio.run(run())

if __name__ == "__main__":
    main()
