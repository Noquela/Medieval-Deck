"""Generators module for AI asset creation."""

# Import generators conditionally to avoid dependency issues
try:
    from .asset_generator import AssetGenerator
    from .prompt_optimizer import PromptOptimizer
    GENERATORS_AVAILABLE = True
except ImportError:
    AssetGenerator = None
    PromptOptimizer = None
    GENERATORS_AVAILABLE = False

__all__ = ["GENERATORS_AVAILABLE"]

if GENERATORS_AVAILABLE:
    __all__.extend(["AssetGenerator", "PromptOptimizer"])
