# Implements: REQ-F-BOOT-001
"""
genesis_sdlc — AI-augmented SDLC toolkit built on abiogenesis.

Provides the standard SDLC bootstrap graph as an importable GTL Package.
"""
__version__ = "0.1.6"

from genesis_sdlc.sdlc_graph import package, worker

__all__ = ["package", "worker", "__version__"]
