"""
Medieval Deck - AI-Generated Card Game

A medieval-themed card game with AI-generated backgrounds using Stable Diffusion XL.
"""

__version__ = "1.0.0"
__author__ = "Bruno"

# Import core modules
try:
    from .models import card_models
    from .game import engine, cards, deck, ui
    from .utils import config, helpers
    
    # Try to import AI modules conditionally
    try:
        from .models import sdxl_pipeline
        from .generators import asset_generator, prompt_optimizer
        AI_MODULES_AVAILABLE = True
    except ImportError:
        AI_MODULES_AVAILABLE = False
        sdxl_pipeline = None
        asset_generator = None
        prompt_optimizer = None
        
except ImportError:
    # If basic modules fail, we have bigger problems
    raise

# Define what gets exported
__all__ = [
    "card_models", 
    "engine",
    "cards",
    "deck", 
    "ui",
    "config",
    "helpers",
    "AI_MODULES_AVAILABLE"
]

# Add AI modules to __all__ if available
if AI_MODULES_AVAILABLE:
    __all__.extend([
        "sdxl_pipeline",
        "asset_generator", 
        "prompt_optimizer"
    ])
