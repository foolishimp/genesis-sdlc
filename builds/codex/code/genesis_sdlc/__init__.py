# Implements: REQ-F-BOOT-001
"""
genesis_sdlc — Codex build of the standard SDLC toolkit.

This build provides the standard SDLC bootstrap graph as an importable GTL
Package while keeping the Codex tenant/runtime surface independent from the
legacy Python/Claude build.
"""

__version__ = "0.5.1"

from genesis_sdlc.sdlc_graph import package, worker

__all__ = ["package", "worker", "__version__"]
