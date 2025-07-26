#!/usr/bin/env python3
"""
Asset Generator Script - Versão Simplificada
Usa os métodos existentes do AssetGenerator
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.generators.asset_generator import AssetGenerator
from src.utils.config import Config
from src.models.sdxl_pipeline import SDXLPipeline


def clean_legacy_assets():
    """Remove assets antigos."""
    print("Cleaning legacy assets...")
    
    legacy_paths = [
        "assets/bg/combat_corridor.png",
        "assets/sheets/knight_idle.png", 
        "assets/sheets/knight_attack.png",
        "assets/sheets/goblin_idle.png",
        "assets/sheets/goblin_attack.png",
        "assets/sheets/skeleton_idle.png",
        "assets/sheets/skeleton_attack.png",
        "assets/sheets/torch_flicker.png",
        "assets/ui/intent_attack.png",
        "assets/ui/intent_defend.png",
        "assets/ui/intent_spell.png"
    ]
    
    for path in legacy_paths:
        if os.path.exists(path):
            os.remove(path)
    
    print("Legacy cleanup complete")


def generate_all_assets():
    """Gera todos os assets usando métodos existentes do AssetGenerator."""
    print("Generating new AI assets...")
    
    # Initialize components
    config = Config()
    pipeline = SDXLPipeline(
        model_id=config.ai.model_id,
        device=config.get_device(),
        cache_dir=str(config.assets_cache_dir),
        memory_efficient=config.ai.memory_efficient
    )
    
    ag = AssetGenerator(
        config=config,
        sdxl_pipeline=pipeline,
        cache_dir=str(config.assets_cache_dir)
    )
    
    # Create directories
    os.makedirs("assets/bg", exist_ok=True)
    os.makedirs("assets/sheets", exist_ok=True) 
    os.makedirs("assets/ui", exist_ok=True)
    
    try:
        # 1. BACKGROUND
        print("\nGenerating backgrounds...")
        background_path = ag.generate_background(force_regenerate=True)
        print(f"Background: {background_path}")
        
        # 2. CHARACTER SPRITES
        print("\nGenerating character sprites...")
        sprites = ag.generate_character_sprites(force_regenerate=True)
        for character, path in sprites.items():
            print(f"{character}: {path}")
        
        # 3. UI ASSETS
        print("\nGenerating UI assets...")
        ui_assets = ag.generate_ui_assets(force_regenerate=True)
        for asset, path in ui_assets.items():
            print(f"{asset}: {path}")
        
        # 4. CARD BACKGROUNDS
        print("\nGenerating card backgrounds...")
        cards = ag.generate_all_card_backgrounds_from_config(force_regenerate=True)
        for card, path in cards.items():
            print(f"{card}: {path}")
        
        print("\nAll assets generated successfully!")
        
    except Exception as e:
        print(f"Error during generation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if pipeline:
            pipeline.unload_models()


def main():
    """Main function."""
    print("Medieval Deck - AI Asset Generator (Simple)")
    print("=" * 50)
    
    try:
        clean_legacy_assets()
        generate_all_assets()
        
    except KeyboardInterrupt:
        print("\nGeneration cancelled by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
