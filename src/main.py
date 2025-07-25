"""
Medieval Deck - Main Game Launcher

AI-powered medieval card game with Stable Diffusion XL background generation.
"""

import sys
import logging
from pathlib import Path
from typing import Optional
import argparse

# Add src to path for imports
src_path = Path(__file__).parent
project_root = src_path.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.utils.config import Config
    from src.utils.helpers import setup_logging, get_system_info
    from src.utils.gpu_compatibility import check_and_fix_gpu_compatibility
    from src.game.engine import GameEngine
    from src.game.ui import GameUI
    
    # Import AI modules conditionally to avoid dependency issues
    try:
        from src.generators.asset_generator import AssetGenerator
        from src.models.sdxl_pipeline import SDXLPipeline
        AI_AVAILABLE = True
    except ImportError as ai_import_error:
        print(f"AI modules not available: {ai_import_error}")
        AI_AVAILABLE = False
        AssetGenerator = None
        SDXLPipeline = None
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Medieval Deck - AI-Generated Card Game",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                     # Start game with default settings
  python main.py --generate-assets  # Generate AI backgrounds for all cards
  python main.py --assets-only      # Generate AI assets and exit (no game)
  python main.py --debug            # Enable debug logging
  python main.py --no-ai            # Disable AI generation
  python main.py --system-info      # Print system information and exit
  python main.py --skip-gpu-check   # Skip automatic GPU compatibility check
  python main.py --force-gpu-fix    # Auto-fix GPU issues without confirmation
        """
    )
    
    parser.add_argument(
        "--config-dir",
        type=str,
        help="Directory containing configuration files"
    )
    
    parser.add_argument(
        "--generate-assets",
        action="store_true",
        help="Generate AI backgrounds for all cards before starting game"
    )
    
    parser.add_argument(
        "--assets-only",
        action="store_true",
        help="Generate AI assets and exit without starting the game"
    )
    
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI generation and use placeholder backgrounds"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file"
    )
    
    parser.add_argument(
        "--window-size",
        type=str,
        metavar="WIDTHxHEIGHT",
        help="Window size (e.g., 1280x720)"
    )
    
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="Start in fullscreen mode"
    )
    
    parser.add_argument(
        "--system-info",
        action="store_true",
        help="Print system information and exit"
    )
    
    parser.add_argument(
        "--skip-gpu-check",
        action="store_true",
        help="Skip automatic GPU compatibility check and fix"
    )
    
    parser.add_argument(
        "--force-gpu-fix",
        action="store_true",
        help="Force GPU compatibility fix without user confirmation"
    )
    
    parser.add_argument(
        "--character-backgrounds",
        action="store_true",
        help="Regenerate character backgrounds with scenery-only prompts"
    )
    
    return parser


def parse_window_size(size_str: str) -> tuple[int, int]:
    """
    Parse window size string.
    
    Args:
        size_str: Size string in format "WIDTHxHEIGHT"
        
    Returns:
        Tuple of (width, height)
    """
    try:
        width, height = size_str.split('x')
        return int(width), int(height)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid window size format: {size_str}. Use WIDTHxHEIGHT (e.g., 1280x720)"
        )


def print_system_info():
    """Print system information for debugging."""
    print("=== Medieval Deck - System Information ===")
    
    info = get_system_info()
    
    print(f"Platform: {info['platform']}")
    print(f"Python: {info['python_version'].split()[0]}")
    print(f"Working Directory: {info['working_directory']}")
    
    if "memory" in info:
        memory = info["memory"]
        print(f"Memory: {memory['total_gb']:.1f} GB total, "
              f"{memory['available_gb']:.1f} GB available ({memory['percent_used']:.1f}% used)")
    
    if "cuda" in info:
        cuda = info["cuda"]
        if cuda["available"]:
            print(f"CUDA: Available - {cuda['device_name']} ({cuda['memory_gb']:.1f} GB)")
            if "cuda_capability" in cuda:
                print(f"CUDA Capability: {cuda['cuda_capability']}")
            if cuda.get("is_rtx_50_series", False):
                print("🔥 RTX 50 Series GPU Detected")
                if cuda.get("requires_pytorch_nightly", False):
                    print("⚠️  Requires PyTorch with CUDA 12.8 for optimal performance")
                elif "+cu128" in cuda.get("pytorch_version", ""):
                    print("✅ Fully optimized with CUDA 12.8 support")
        else:
            print(f"CUDA: Not available")
            if "error" in cuda:
                print(f"CUDA Error: {cuda['error']}")
    
    print("=" * 45)


def initialize_ai_pipeline(config: Config, enable_ai: bool) -> Optional[object]:
    """
    Initialize AI pipeline if enabled.
    
    Args:
        config: Configuration object
        enable_ai: Whether to enable AI generation
        
    Returns:
        Initialized SDXL pipeline or None
    """
    if not enable_ai or not AI_AVAILABLE:
        logging.info("AI generation disabled or not available")
        return None
        
    logging.info("Initializing AI pipeline...")
    
    if not AI_AVAILABLE:
        logging.error("AI modules not available")
        return None
    
    try:
        pipeline = SDXLPipeline(
            model_id=config.ai.model_id,
            refiner_id=config.ai.refiner_id,
            enable_refiner=config.ai.enable_refiner,
            device=config.get_device(),
            cache_dir=str(config.assets_cache_dir),
            memory_efficient=config.ai.memory_efficient
        )
        
        logging.info("AI pipeline initialized successfully")
        return pipeline
        
    except Exception as e:
        logging.error(f"Failed to initialize AI pipeline: {e}")
        logging.warning("Continuing without AI generation")
        return None


def generate_initial_assets(
    config: Config,
    pipeline: Optional[object],
    force_generate: bool = False
) -> None:
    """
    Generate initial card backgrounds.
    
    Args:
        config: Configuration object
        pipeline: SDXL pipeline
        force_generate: Force generation even if AI is disabled
    """
    if pipeline is None and not force_generate:
        logging.info("Skipping asset generation (AI disabled)")
        return
        
    logging.info("Starting initial asset generation...")
    
    try:
        # Initialize asset generator
        asset_generator = AssetGenerator(
            config=config,
            sdxl_pipeline=pipeline,
            cache_dir=str(config.assets_cache_dir)
        )
        
        # Generate all card backgrounds from configuration
        generated_paths = asset_generator.generate_all_card_backgrounds_from_config(
            force_regenerate=force_generate
        )
        
        if generated_paths:
            logging.info(f"Successfully generated {len(generated_paths)} card backgrounds")
            for card_id, path in generated_paths.items():
                logging.debug(f"  {card_id}: {path}")
        else:
            logging.warning("No card backgrounds were generated")
        
    except Exception as e:
        logging.error(f"Failed to generate initial assets: {e}")


def regenerate_character_backgrounds(
    config: Config,
    pipeline: Optional[object],
    force_generate: bool = True
) -> None:
    """
    Regenera backgrounds específicos dos personagens com cenários apenas.
    
    Args:
        config: Configuration object
        pipeline: SDXL pipeline
        force_generate: Force generation even if exists
    """
    if pipeline is None:
        logging.error("AI pipeline not available for character background generation")
        return
        
    logging.info("Starting character background regeneration...")
    
    try:
        # Initialize asset generator
        asset_generator = AssetGenerator(
            config=config,
            sdxl_pipeline=pipeline,
            cache_dir=str(config.assets_cache_dir)
        )
        
        # Generate character backgrounds with new scenery-only prompts
        generated_paths = asset_generator.generate_character_backgrounds(
            force_regenerate=force_generate
        )
        
        if generated_paths:
            logging.info(f"Successfully regenerated {len(generated_paths)} character backgrounds")
            for character_id, path in generated_paths.items():
                logging.info(f"  {character_id}: {path}")
        else:
            logging.warning("No character backgrounds were generated")
        
    except Exception as e:
        logging.error(f"Failed to regenerate character backgrounds: {e}")


def main():
    """Main entry point for Medieval Deck game."""
    # Parse command line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Print system info if requested
    if args.system_info:
        print_system_info()
        return 0
        
    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger = setup_logging(
        level=log_level,
        log_file=args.log_file
    )
    
    logger.info("Starting Medieval Deck...")
    
    # GPU Compatibility Check - Auto-fix RTX 50 series issues
    if not args.skip_gpu_check:
        logger.info("Checking GPU compatibility...")
        try:
            gpu_compatible = check_and_fix_gpu_compatibility(
                auto_fix=True,
                interactive=not args.force_gpu_fix  # Skip confirmation if forced
            )
            if not gpu_compatible:
                logger.warning("GPU compatibility issues detected but not fixed")
                logger.warning("AI generation may not work properly")
        except Exception as e:
            logger.error(f"Error during GPU compatibility check: {e}")
            logger.warning("Continuing without GPU compatibility verification")
    else:
        logger.info("Skipping GPU compatibility check (--skip-gpu-check)")
    
    try:
        # Initialize configuration
        config = Config(config_dir=args.config_dir)
        
        # Apply command line overrides
        if args.window_size:
            width, height = parse_window_size(args.window_size)
            config.update_ui_config(window_width=width, window_height=height)
            
        if args.fullscreen:
            config.update_ui_config(fullscreen=True)
            
        # Initialize AI pipeline
        enable_ai = not args.no_ai
        ai_pipeline = initialize_ai_pipeline(config, enable_ai)
        
        # Skip automatic asset generation - only generate if explicitly requested
        if args.generate_assets:
            generate_initial_assets(config, ai_pipeline, force_generate=True)
        else:
            logging.info("Skipping automatic asset generation - using existing images")
        
        # Se for modo apenas assets, sair após gerar
        if args.assets_only:
            generate_initial_assets(config, ai_pipeline, force_generate=True)
            logging.info("Assets generation completed. Exiting without starting game.")
            return 0
            
        # Se for regenerar backgrounds dos personagens, sair após gerar
        if args.character_backgrounds:
            regenerate_character_backgrounds(config, ai_pipeline, force_generate=True)
            logging.info("Character backgrounds regeneration completed. Exiting without starting game.")
            return 0
            
        # Initialize game engine
        logger.info("Initializing game engine...")
        game_engine = GameEngine(config=config)
        
        # Initialize UI
        logger.info("Initializing game UI...")
        game_ui = GameUI(
            config=config,
            game_engine=game_engine,
            asset_generator=AssetGenerator(
                config=config,
                sdxl_pipeline=ai_pipeline
            ) if ai_pipeline and AI_AVAILABLE and AssetGenerator else None
        )
        
        # Start game
        logger.info("Starting game loop...")
        return game_ui.run()
        
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
        
    finally:
        logger.info("Medieval Deck shutting down")


if __name__ == "__main__":
    sys.exit(main())
