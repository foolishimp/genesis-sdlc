# Implements: REQ-F-CORE-001
"""
fp_dispatch — MCP transport for F_P actor invocations.

Architecture: F_D → MCP → F_P.claudecode (ADR-020)
Transport: @steipete/claude-code-mcp (stdio MCP server) via Python mcp SDK

This module is the single MCP transport implementation. Both the engine
(__main__.py) and the test harness (scenario_helpers.py) import from here.
If the tests pass, the production code path is proven — same code, same path.

No subprocess fallback for F_P. `claude -p` is not used for F_P. Ever.
See ADR-020 (ported from ai_sdlc_method ADR-023).
"""
from __future__ import annotations

import subprocess


def has_mcp_transport() -> bool:
    """Check if @steipete/claude-code-mcp is available for F_P dispatch.

    Returns True if npx can resolve the package. Does not start the server.
    """
    try:
        subprocess.run(
            ["npx", "@steipete/claude-code-mcp", "--help"],
            capture_output=True, text=True, timeout=15,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def call_claude_code_mcp(prompt: str, work_folder: str) -> str:
    """Invoke claude_code tool via @steipete/claude-code-mcp MCP server.

    Architecture: F_D → MCP → F_P.claudecode
    Transport: stdio JSON-RPC via Python mcp SDK → npx @steipete/claude-code-mcp

    The actor receives full tool access via MCP and can write artifacts
    directly to the workspace. The caller should check whether the actor
    wrote files before assuming the return value contains the artifact.

    Raises:
        ImportError: if the mcp Python SDK is not installed.
        RuntimeError: if the MCP call fails.
    """
    import asyncio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def _invoke() -> str:
        server_params = StdioServerParameters(
            command="npx",
            args=["@steipete/claude-code-mcp"],
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "claude_code",
                    arguments={
                        "prompt": prompt,
                        "workFolder": work_folder,
                    },
                )
                # Extract text content from MCP result
                parts = []
                for block in result.content:
                    if hasattr(block, "text"):
                        parts.append(block.text)
                return "\n".join(parts)

    return asyncio.run(_invoke())
