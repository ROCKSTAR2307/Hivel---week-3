# MCP Server Suite 🛠️

This project provides a suite of Meta-Control Protocol (MCP) servers and agents designed for querying and analyzing data related to code repositories, specifically focusing on commits and pull requests. It offers a flexible and extensible architecture for building AI-powered tools that can understand and reason about code changes. The core idea is to expose data and functionality through MCP servers, allowing agents to interact with them using a standardized protocol. This enables the creation of sophisticated analysis pipelines and automated workflows.

🚀 **Key Features**

*   **Commit Data Analysis**: Provides tools to query commit summaries, counts, and details over specified time periods. Enables custom SQL queries for advanced analysis.
*   **Pull Request Analysis**: Offers tools to retrieve PR summaries, review times, cycle times, and churn metrics. Supports filtering PRs by cycle time and executing custom SQL queries.
*   **AI Agent Integration**: Designed to work seamlessly with AI agents, allowing them to access and analyze commit and PR data through a standardized MCP interface.
*   **Read-Only Data Access**: Enforces read-only access to the database, preventing unauthorized data modification.
*   **Asynchronous Operations**: Utilizes `asyncio` for efficient and non-blocking operations.
*   **Centralized Management**: The `manager.py` script orchestrates the entire application, managing the lifecycle of the MCP servers and agents.
*   **Audit Logging**: Logs agent starts, user queries, tool calls, and SQL statements for auditing and debugging purposes.
*   **Time-Based Filtering**: Provides a flexible time filtering mechanism to retrieve data within specific time ranges.
*   **Environment Variable Configuration**: Uses `.env` files to manage configuration settings.

🛠️ **Tech Stack**

| Category      | Technology           | Description                                                                 |
|---------------|----------------------|-----------------------------------------------------------------------------|
| Backend       | Python               | Core programming language.                                                  |
| Database      | PostgreSQL           | Relational database for storing commit and PR data.                          |
| MCP Framework | `mcp.server.fastmcp` | Framework for building MCP servers.                                         |
| Async         | `asyncio`            | Asynchronous programming library.                                           |
| Database      | `psycopg2`           | PostgreSQL adapter for Python.                                              |
| Environment   | `dotenv`             | For loading environment variables from `.env` files.                         |
| Logging       | Custom `audit_logger`| Custom module for logging events.                                           |
| Time          | `datetime`, `timedelta`| For time-related calculations and filtering.                                |
| Agents        | Custom `agents` module| Custom module containing the `Agent` and `Runner` classes.                   |
| File Handling | `pathlib`            | For working with file paths.                                                |
| Input/Output  | `sys`                | For accessing command-line arguments and standard input/output.             |
| Regex         | `re`                 | For regular expression matching (e.g., SQL validation).                      |
| Inspection    | `inspect`            | For inspecting live objects.                                                |
| Type Hints    | `typing`             | For type hinting.                                                           |

📦 **Getting Started / Setup Instructions**

### Prerequisites

*   Python 3.7+
*   PostgreSQL database
*   `pip` package manager

### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**

    *   Create a `.env` file in the root directory.
    *   Add the following environment variables, replacing the placeholders with your actual values:

        ```
        DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
        ORG_ALLOWED=2133 # Example value
        ```

        Make sure that the database is running and accessible.

### Running Locally

1.  **Start the MCP servers and agents:**

    ```bash
    python mcp_server/manager.py "Your initial prompt here"
    ```

    Replace `"Your initial prompt here"` with the initial query you want to run. You can also run it without an initial prompt and enter prompts interactively.

📂 **Project Structure**

```
├── mcp_server/
│   ├── __init__.py
│   ├── up_commit_server.py  # MCP server for commit data
│   ├── manager.py           # Main entry point, manages servers and agents
│   ├── database.py          # Database connection and query execution
│   ├── up_commit_agent.py   # Agent for interacting with the commit server
│   ├── pr_agent.py          # Agent for interacting with the PR server
│   ├── up_pr_server.py      # MCP server for PR data
│   ├── up_commit_tools.py   # Implementation of commit analysis tools
│   ├── up_pr_tools.py      # Implementation of PR analysis tools
│   ├── audit_logger.py      # Logging mechanism
│   ├── time_filter.py       # Time period parsing and filtering
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables (not committed to repo)
├── README.md              # This file
```


🤝 **Contributing**

We welcome contributions to this project! Please follow these guidelines:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and write tests.
4.  Ensure all tests pass.
5.  Submit a pull request with a clear description of your changes.



💖 **Thanks**

Thank you for your interest in this project! We hope it helps you build amazing AI-powered tools for analyzing code repositories.

This is written by [readme.ai](https://readme-generator-phi.vercel.app/).
