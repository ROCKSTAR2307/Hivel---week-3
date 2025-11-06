from pathlib import Path
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import sys
import asyncio
from agents.extensions.visualization import draw_graph
from bot_message import BOT_SYSTEM_MESSAGE
from audit_logger import log_agent_start, log_user_query

def main() -> None:
    base_dir = Path(__file__).resolve().parent
    load_dotenv(base_dir.parent / ".env")
    asyncio.run(run())


async def run() -> None:
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    async with MCPServerStdio(
        params={
            "command": sys.executable,
            "args": ["-m", "mcp_server.up_pr_server"],
            "cwd": str(project_root),
        },
    ) as server:
        log_agent_start("pr_agent")

        agent = Agent(
            name="pr_agent",
            model="gpt-4.1-mini",
            instructions=BOT_SYSTEM_MESSAGE,
            mcp_servers=[server],
        )

        prompt = "give me the review duration for the pr id 261"
        log_user_query("pr_agent", prompt)
        result = await Runner.run(agent, prompt)
        print(result.final_output)
        #draw_graph(agent, filename="agent_graph")

if __name__ == "__main__":
    main()
