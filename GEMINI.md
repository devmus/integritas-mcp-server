# Gemini Project Instructions: integritas-mcp-server

This document provides instructions for the Gemini AI assistant to effectively contribute to this project.

## Project Overview

This project is the Integritas MCP Server. Its primary function appears to be providing a "stamp-only" service. It can be run as a standard MCP service over stdio or as an HTTP server for development purposes.

## Key Technologies

- **Python Version:** >=3.12
- **Frameworks:** FastAPI, Typer, Pydantic
- **HTTP Client:** HTTPX
- **Testing:** Pytest, pytest-asyncio, respx
- **Linting/Formatting:** Ruff
- **Type Checking:** MyPy
- **Dependency Management:** uv

## Commands

- **Run (stdio):** `integritas-mcp stdio`
- **Run (HTTP dev server):** `integritas-mcp http --host 0.0.0.0 --port 8787`
- **Run Tests:** `pytest -q`
- **Run Linter/Formatter:** `ruff check .` and `ruff format .`
- **Run Type Checker:** `mypy .`
- **Generate Schemas:** `python scripts/generate_schemas.py`
- **Install Dependencies:** `uv pip install -e .[dev]`

## Coding Conventions

- **Style Guide:** Follow the configuration in the `[tool.ruff]` section of `pyproject.toml`.
- **Type Safety:** Adhere to the MyPy rules defined in the `[tool.mypy]` section of `pyproject.toml`. All new code should include type hints.
- **Modularity:** Place business logic for different services in separate files within `src/integritas_mcp_server/services/`.

## File Structure

- **Source Code:** All Python source code should be located in `src/integritas_mcp_server/`.
- **Tests:** All tests should be located in the `tests/` directory. New test files should be named `test_*.py`.
- **Scripts:** Utility or generation scripts should be placed in the `scripts/` directory.
