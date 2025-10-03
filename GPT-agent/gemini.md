# Gemini Project Instructions: Integritas MCP Server GPT Agent

This document provides context for the files related to the Integritas OpenAI custom GPT.

The relevant files for understanding the agent's capabilities are:

*   `gpt-playbook.md`: This file outlines the high-level instructions and workflows for the GPT agent. It describes the conceptual flows for "stamping" and "verifying" data, including the expected sequences of actions and user interactions. It also contains important behavioral rules and guardrails for the agent.

*   `gpt-schema.json`: This file is an OpenAPI 3.1.1 specification that defines the concrete API endpoints the agent can use. It details the server URL, paths, operation IDs (`stamp_start`, `stamp_status`, `verify_data`), request bodies, and response schemas for each action. This file provides the technical, machine-readable definition of the agent's tools.

*   `api-req-res.md`: This file provides concrete examples of the request and response payloads for each of the main API actions. It serves as a practical guide to the data structures involved in API communication.

*   `resources.md`: This file contains links to OpenAI documentation on creating and building custom GPTs.

In summary, `gpt-playbook.md` explains the "how" and "why" from a user-interaction perspective, `gpt-schema.json` provides the formal API specification, and `api-req-res.md` gives concrete examples. These files are essential for understanding the complete functionality of the GPT agent.