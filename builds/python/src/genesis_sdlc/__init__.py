# Implements: REQ-F-BOOT-001
"""
genesis_sdlc — AI-augmented SDLC toolkit built on abiogenesis.

Provides the standard SDLC bootstrap graph as an importable GTL Package.
``package`` and ``worker`` are loaded lazily so that the installer can
be imported without GTL on the path (bootstrap hermiticity).
"""
__version__ = "1.0.0b1"

__all__ = ["package", "worker", "__version__"]


def __getattr__(name: str):
    if name in ("package", "worker"):
        from genesis_sdlc.sdlc_graph import package, worker
        globals()["package"] = package
        globals()["worker"] = worker
        return globals()[name]
    raise AttributeError(f"module 'genesis_sdlc' has no attribute {name!r}")
