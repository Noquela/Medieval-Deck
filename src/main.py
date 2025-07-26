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
        help="Directory containing configuration de s"
    )
    
    parser.add_argument(
        "--generate-assets",
        action="store_true",
        help="Generate AI backgrounds for all carde efore starting game"
    )
    
    parser.add_argument(
        "--assets-only",
        action="store_true",
        help="Generate AI assets and exit without starting the game"
    )
    
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI generation and use placede er backgrounds"
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
    
    parser.add_argument(
        "--cinematic-assets",
        action="store_true", 
        help="Generate all cinematic assets (4K backgrounds, sprites, UI elements)"
    )
    
    parser.add_argument(
        "--regenerate-hd",
        action="store_true",
        help="Regenerate all existing backgrounds in 3440x1440 ultrawide with enhanced prompts"
    )
    
    parser.add_argument(
        "--transparent-sprites",
        action="store_true",
        help="Generate transparent character sprites for background integration"
    )
    
    parser.add_argument(
        "--process-sprites",
        action="store_true",
        help="Process existing sprites to remove background using AI"
    )
    
    parser.add_argument(
        "--demo-turn-engine",
        action="store_true",
        help="Run Turn Engine demo (Fase 1 implementation)"
    )
    
    parser.add_argument(
        "--demo-gameplay",
        action="store_true",
        help="Run complete Gameplay demo (Fase 2 implementation)"
    )
    
    parser.add_argument(
        "--demo-intelligent-combat",
        action="store_true",
        help="Run Intelligent Combat demo (Fase 3 implementation)"
    )
    
    parser.add_argument(
        "--demo-combat-ui",
        action="store_true",
        help="Run Combat UI demo (Fase 4 implementation)"
    )
    
    parser.add_argument(
        "--generate-mvp-assets",
        action="store_true",
        help="Generate MVP assets (2 biomes, 3 characters, UI elements)"
    )
    
    parser.add_argument(
        "--demo-mvp-combat",
        action="store_true",
        help="Run MVP Combat demo with AI-generated backgrounds"
    )
    
    parser.add_argument(
        "--skip-select",
        action="store_true",
        help="Skip character selection and go directly to MVP Combat"
    )
    
    parser.add_argument(
        "--gen-assets-full",
        action="store_true",
        help="Generate all assets with custom corridor background and sprite sheets"
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


def generate_cinematic_assets(
    config: Config,
    pipeline: Optional[object],
    force_generate: bool = True
) -> None:
    """
    Gera todos os assets cinematográficos: backgrounds 4K, sprites e UI.
    
    Args:
        config: Configuration object
        pipeline: SDXL pipeline
        force_generate: Force generation even if exists
    """
    if pipeline is None:
        logging.error("AI pipeline not available for cinematic asset generation")
        return
        
    logging.info("🎬 Starting cinematic asset generation...")
    
    try:
        # Initialize asset generator
        asset_generator = AssetGenerator(
            config=config,
            sdxl_pipeline=pipeline,
            cache_dir=str(config.assets_cache_dir)
        )
        
        # Generate all cinematic assets
        results = asset_generator.generate_all_cinematic_assets(
            force_regenerate=force_generate
        )
        
        # Log results
        if results:
            total_assets = sum(len(category) for category in results.values())
            logging.info(f"🎉 Successfully generated {total_assets} cinematic assets!")
            
            for category, assets in results.items():
                if assets:
                    logging.info(f"  {category.title()}:")
                    for asset_id, path in assets.items():
                        logging.info(f"    {asset_id}: {path}")
        else:
            logging.warning("No cinematic assets were generated")
        
    except Exception as e:
        logging.error(f"Failed to generate cinematic assets: {e}")


def regenerate_hd_backgrounds(
    config: Config,
    pipeline: Optional[object],
    force_generate: bool = True
) -> None:
    """
    Regenera todos os backgrounds existentes em 3440x1440 ultrawide com prompts melhorados.
    
    Args:
        config: Configuration object
        pipeline: SDXL pipeline
        force_generate: Force generation even if exists
    """
    if pipeline is None:
        logging.error("AI pipeline not available for HD background regeneration")
        return
        
    logging.info("🎬 Starting HD background regeneration (3440x1440)...")
    
    try:
        # Initialize asset generator
        asset_generator = AssetGenerator(
            config=config,
            sdxl_pipeline=pipeline,
            cache_dir=str(config.assets_cache_dir)
        )
        
        # Regenerate all backgrounds in HD ultrawide
        results = asset_generator.regenerate_all_backgrounds_hd_ultrawide(
            force_regenerate=force_generate
        )
        
        # Log results
        if results:
            total_assets = len(results)
            logging.info(f"🎉 Successfully regenerated {total_assets} HD backgrounds!")
            
            for asset_type, assets in results.items():
                logging.info(f"  {asset_type}: {assets}")
        else:
            logging.warning("No HD backgrounds were regenerated")
        
    except Exception as e:
        logging.error(f"Failed to regenerate HD backgrounds: {e}")


def generate_transparent_sprites(
    config: Config,
    pipeline: Optional[object],
    force_generate: bool = True
) -> None:
    """
    Gera sprites transparentes de personagens para integração com background.
    
    Args:
        config: Configuration object
        pipeline: SDXL pipeline
        force_generate: Force generation even if exists
    """
    if pipeline is None:
        logging.error("AI pipeline not available for transparent sprite generation")
        return
        
    logging.info("🎭 Starting transparent character sprites generation...")
    
    try:
        # Initialize asset generator
        asset_generator = AssetGenerator(
            config=config,
            sdxl_pipeline=pipeline,
            cache_dir=str(config.assets_cache_dir)
        )
        
        # Generate transparent sprites
        results = asset_generator.generate_transparent_character_sprites(
            force_regenerate=force_generate
        )
        
        # Log results
        if results:
            total_sprites = len(results)
            logging.info(f"🎉 Successfully generated {total_sprites} transparent sprites!")
            
            for sprite_id, path in results.items():
                logging.info(f"  {sprite_id}: {path}")
        else:
            logging.warning("No transparent sprites were generated")
        
    except Exception as e:
        logging.error(f"Failed to generate transparent sprites: {e}")


def process_existing_sprites(
    config: Config,
    force_generate: bool = True
) -> None:
    """
    Processa sprites existentes para remover fundo usando AI.
    
    Args:
        config: Configuration object
        force_generate: Force processing even if transparent versions exist
    """
    logging.info("🎨 Starting background removal for existing sprites...")
    
    try:
        # Initialize asset generator (sem pipeline pois não vamos gerar)
        asset_generator = AssetGenerator(
            config=config,
            sdxl_pipeline=None,
            cache_dir=str(config.assets_cache_dir)
        )
        
        # Process existing sprites
        results = asset_generator.process_existing_sprites_remove_background(
            force_regenerate=force_generate
        )
        
        # Log results
        if results:
            total_sprites = len(results)
            logging.info(f"🎉 Successfully processed {total_sprites} sprites!")
            
            for sprite_id, path in results.items():
                logging.info(f"  {sprite_id}: {path}")
        else:
            logging.warning("No sprites were processed")
        
    except Exception as e:
        logging.error(f"Failed to process existing sprites: {e}")


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
            
        # Store skip_select flag in config for GameUI to access
        config.skip_select = getattr(args, 'skip_select', False)
            
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
            
        # Se for gerar assets cinematográficos, sair após gerar
        if args.cinematic_assets:
            generate_cinematic_assets(config, ai_pipeline, force_generate=True)
            logging.info("Cinematic assets generation completed. Exiting without starting game.")
            return 0
            
        # Se for regenerar backgrounds em HD ultrawide, sair após gerar
        if args.regenerate_hd:
            regenerate_hd_backgrounds(config, ai_pipeline, force_generate=True)
            logging.info("HD backgrounds regeneration completed. Exiting without starting game.")
            return 0
            
        # Se for gerar sprites transparentes, sair após gerar
        if args.transparent_sprites:
            generate_transparent_sprites(config, ai_pipeline, force_generate=True)
            logging.info("Transparent sprites generation completed. Exiting without starting game.")
            return 0
            
        # Se for processar sprites existentes, sair após processar
        if args.process_sprites:
            process_existing_sprites(config, force_generate=True)
            logging.info("Sprite processing completed. Exiting without starting game.")
            return 0
            
        # Se for executar demo do Turn Engine
        if args.demo_turn_engine:
            logging.info("Running Turn Engine demo...")
            try:
                from demo_turn_engine import demo_turn_engine
                demo_turn_engine()
                logging.info("Turn Engine demo completed.")
                return 0
            except ImportError as e:
                logging.error(f"Failed to import Turn Engine demo: {e}")
                return 1
        
        # Se for executar demo do Gameplay completo
        if args.demo_gameplay:
            logging.info("Running complete Gameplay demo...")
            try:
                from demo_gameplay import main as demo_gameplay_main
                result = demo_gameplay_main()
                logging.info("Gameplay demo completed.")
                return 0 if result else 1
            except ImportError as e:
                logging.error(f"Failed to import Gameplay demo: {e}")
                return 1
        
        # Se for executar demo do Combate Inteligente
        if args.demo_intelligent_combat:
            logging.info("Running Intelligent Combat demo...")
            try:
                from demo_intelligent_combat import main as demo_intelligent_combat_main
                result = demo_intelligent_combat_main()
                logging.info("Intelligent Combat demo completed.")
                return 0 if result else 1
            except ImportError as e:
                logging.error(f"Failed to import Intelligent Combat demo: {e}")
                return 1
                
        # Se for executar demo da UI de Combate
        if args.demo_combat_ui:
            logging.info("Running Combat UI demo...")
            try:
                from demo_combat_ui import main as demo_combat_ui_main
                result = demo_combat_ui_main()
                logging.info("Combat UI demo completed.")
                return 0 if result else 1
            except ImportError as e:
                logging.error(f"Failed to import Combat UI demo: {e}")
                return 1
        
        # Se for gerar assets do MVP
        if args.generate_mvp_assets:
            logging.info("Running MVP asset generation...")
            try:
                import subprocess
                result = subprocess.run([sys.executable, "scripts/generate_mvp_assets.py"], 
                                      capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print("Errors:", result.stderr)
                logging.info("MVP asset generation completed.")
                return result.returncode
            except Exception as e:
                logging.error(f"Failed to run MVP asset generation: {e}")
                return 1
        
        # Se for executar demo MVP de combate
        if args.demo_mvp_combat:
            logging.info("Running MVP Combat demo...")
            try:
                from demo_mvp_combat import main as demo_mvp_combat_main
                result = demo_mvp_combat_main()
                logging.info("MVP Combat demo completed.")
                return 0 if result else 1
            except ImportError as e:
                logging.error(f"Failed to import MVP Combat demo: {e}")
                return 1
        
        # Se for gerar assets completos com corredor e sprite sheets
        if args.gen_assets_full:
            logging.info("Running full asset generation...")
            try:
                import subprocess
                result = subprocess.run([sys.executable, "scripts/gen_assets_simple.py"], 
                                      capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print("Errors:", result.stderr)
                logging.info("Full asset generation completed.")
                return result.returncode
            except Exception as e:
                logging.error(f"Failed to run full asset generation: {e}")
                return 1
            
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
