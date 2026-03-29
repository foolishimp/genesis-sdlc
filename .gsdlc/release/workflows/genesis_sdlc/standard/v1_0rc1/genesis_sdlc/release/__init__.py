# Implements: REQ-F-BOOT-001
"""Release/bootstrap surfaces for the Abiogenesis/Python realization."""

from .bootloader import synthesize_bootloader
from .install import VERSION, install
from .wrapper import load_project_requirements, render_wrapper

__all__ = [
    "VERSION",
    "install",
    "load_project_requirements",
    "render_wrapper",
    "synthesize_bootloader",
]
