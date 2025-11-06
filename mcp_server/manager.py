import asyncio
import sys
from pathlib import Path
from contextlib import AsyncExitStack
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from manager_instructions import MANAGER_AGENT_INSTRUCTIONS
from audit_logger import log_agent_start, log_user_query



def main() -> None:
    asyncio.run(run())


async def run() -> None:
    base_dir = Path(__file__).resolve().parent
    load_dotenv(base_dir / ".env")
    load_dotenv(base_dir.parent / ".env")

    project_root = base_dir.parent

    async with AsyncExitStack() as stack:
        pr_server = await stack.enter_async_context(
            MCPServerStdio(
                params={
                    "command": sys.executable,
                    "args": ["-m", "mcp_server.up_pr_server"],
                    "cwd": str(project_root),
                },
            )
        )

        commit_server = await stack.enter_async_context(
            MCPServerStdio(
                params={
                    "command": sys.executable,
                    "args": ["-m", "mcp_server.up_commit_server"],
                    "cwd": str(project_root),
                },
            )
        )

        manager_agent = Agent(
            name="manager_agent",
            model="gpt-4.1-mini",
            instructions=MANAGER_AGENT_INSTRUCTIONS,
            mcp_servers=[pr_server, commit_server],
        )

        log_agent_start("manager_agent")

        async def handle_prompt(prompt: str) -> None:
            log_user_query("manager_agent", prompt)
            result = await Runner.run(manager_agent, prompt)
            if result.final_output:
                print(result.final_output)
            if getattr(result, "new_messages", None):
                for message in result.new_messages:
                    if message.content:
                        print(f"- {message.content}")

        initial_prompts = []
        if len(sys.argv) > 1:
            initial_prompts.append(" ".join(sys.argv[1:]))
        elif sys.stdin and not sys.stdin.isatty():
            buffered = sys.stdin.read().strip()
            if buffered:
                initial_prompts.append(buffered)

        if initial_prompts:
            for prompt in initial_prompts:
                await handle_prompt(prompt)
            return

        while True:
            try:
                user_prompt = input("How can I help with your PR/commit metrics? (type 'exit' to quit) ").strip()
            except EOFError:
                break

            if not user_prompt:
                continue

            if user_prompt.lower() in {"exit", "quit", "q"}:
                print("Exiting manager. Goodbye!")
                break

            await handle_prompt(user_prompt)


if __name__ == "__main__":
    main()
