"""
Medieval Deck - AI-Generated Card Game

A medieval-themed card game with AI-generated backgrounds using Stable Diffusion XL.
"""

__version__ = "1.0.0"
__author__ = "Bruno"

# Core modules are imported on demand to avoid dependencies
# Import only what's needed for each specific feature

AI_MODULES_AVAILABLE = False
PYGAME_AVAILABLE = False

# Check for optional dependencies
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pass

try:
    import torch
    import diffusers
    AI_MODULES_AVAILABLE = True
except ImportError:
    pass

# Define what gets exported
__all__ = [
    "AI_MODULES_AVAILABLE",
    "PYGAME_AVAILABLE"
]

# Add AI modules to __all__ if available
if AI_MODULES_AVAILABLE:
    __all__.extend([
        "sdxl_pipeline",
        "asset_generator", 
        "prompt_optimizer"
    ])
