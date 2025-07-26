#!/usr/bin/env python3
"""
Asset Generator Script - Regenera todos os assets por IA
Cenário corredor + Sprite sheets + UI elements
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
    """Remove old assets to make room for new AI-generated ones."""
    print("🧹 Cleaning legacy assets...")
    
    # Remove old backgrounds (keep menu backgrounds)
    bg_dir = Path("assets/bg")
    if bg_dir.exists():
        for file in bg_dir.glob("*.png"):
            if "menu" not in file.name.lower():
                print(f"  Removing: {file}")
                file.unlink()
    
    # Remove old sprite sheets
    sheets_dir = Path("assets/sheets")
    if sheets_dir.exists():
        for file in sheets_dir.glob("*.png"):
            if any(name in file.name.lower() for name in ["goblin", "knight", "skeleton"]):
                print(f"  Removing: {file}")
                file.unlink()
    
    print("✔️  Legacy cleanup complete")


def generate_all_assets():
    """Generate all new AI assets with consistent seed."""
    print("🎨 Generating new AI assets...")
    
    # Initialize AI pipeline
    config = Config()
    pipeline = SDXLPipeline(
        model_id=config.ai.model_id,
        refiner_id=config.ai.refiner_id,
        enable_refiner=config.ai.enable_refiner,
        device=config.get_device(),
        cache_dir=str(config.assets_cache_dir),
        memory_efficient=config.ai.memory_efficient
    )
    
    ag = AssetGenerator(
        config=config,
        sdxl_pipeline=pipeline,
        cache_dir=str(config.assets_cache_dir)
    )
    
    # Ensure directories exist
    os.makedirs("assets/bg", exist_ok=True)
    os.makedirs("assets/sheets", exist_ok=True)
    os.makedirs("assets/ui", exist_ok=True)
    
    print("\n📍 Generating background...")
    # BACKGROUND CORREDOR - usar método correto do AssetGenerator
    try:
        background_path = ag.generate_background(force_regenerate=True)
        print(f"✅ Background generated: {background_path}")
    except Exception as e:
        print(f"❌ Background error: {e}")
        return
    
    print("\n⚔️  Generating knight sprite sheets...")
    # KNIGHT IDLE SHEET (10 frames horizontal)
    ag.generate_image(
        prompt=("sprite sheet of valiant medieval knight in gold-trim armor, "
                "idle breathing animation, 10 frames horizontal sequence, "
                "side view, consistent character, pixel art style, "
                "transparent background, high quality"),
        out_path="assets/sheets/knight_idle.png",
        width=5120,  # 10 frames * 512px each
        height=512,
        steps=80,
        cfg_scale=8.5
    )
    
    # KNIGHT ATTACK SHEET
    ag.generate_image(
        prompt=("sprite sheet of valiant medieval knight in gold-trim armor, "
                "sword slash attack animation, 10 frames horizontal sequence, "
                "dynamic motion, side view, consistent character, "
                "transparent background, high quality"),
        out_path="assets/sheets/knight_attack.png",
        width=5120,
        height=512,
        steps=80,
        cfg_scale=8.5
    )
    
    print("\n👹 Generating goblin sprite sheets...")
    # GOBLIN IDLE SHEET
    ag.generate_image(
        prompt=("sprite sheet of goblin scout in leather armor, "
                "idle sneering animation, 10 frames horizontal sequence, "
                "menacing pose, side view, consistent character, "
                "transparent background, high quality"),
        out_path="assets/sheets/goblin_idle.png",
        width=4200,  # 10 frames * 420px each
        height=420,
        steps=80,
        cfg_scale=8.5
    )
    
    # GOBLIN ATTACK SHEET
    ag.generate_image(
        prompt=("sprite sheet of goblin scout in leather armor, "
                "stab attack animation, 10 frames horizontal sequence, "
                "aggressive motion, side view, consistent character, "
                "transparent background, high quality"),
        out_path="assets/sheets/goblin_attack.png",
        width=4200,
        height=420,
        steps=80,
        cfg_scale=8.5
    )
    
    print("\n💀 Generating skeleton sprite sheets...")
    # SKELETON IDLE SHEET
    ag.generate_image(
        prompt=("sprite sheet of skeleton warrior with rusty sword, "
                "idle swaying animation, 10 frames horizontal sequence, "
                "menacing undead pose, side view, consistent character, "
                "transparent background, high quality"),
        out_path="assets/sheets/skeleton_idle.png",
        width=4200,
        height=420,
        steps=80,
        cfg_scale=8.5
    )
    
    # SKELETON ATTACK SHEET
    ag.generate_image(
        prompt=("sprite sheet of skeleton warrior with rusty sword, "
                "overhead slash attack animation, 10 frames horizontal sequence, "
                "powerful strike motion, side view, consistent character, "
                "transparent background, high quality"),
        out_path="assets/sheets/skeleton_attack.png",
        width=4200,
        height=420,
        steps=80,
        cfg_scale=8.5
    )
    
    print("\n🔥 Generating torch animation...")
    # TOCHA ANIMADA (4 frames)
    ag.generate_image(
        prompt=("sprite sheet of medieval wall torch flame, "
                "flickering fire animation, 4 frames horizontal sequence, "
                "warm orange flame, stone wall torch, "
                "transparent background, high quality"),
        out_path="assets/ui/torch_sheet.png",
        width=1024,  # 4 frames * 256px each
        height=256,
        steps=60,
        cfg_scale=8.0
    )
    
    print("\n🗡️  Generating UI icons...")
    # SWORD ICON
    ag.generate_image(
        prompt=("small flat icon of medieval sword pointing up, "
                "gold outline, simple design, game UI element, "
                "transparent background, 64x64 pixels"),
        out_path="assets/ui/icon_sword.png",
        width=64,
        height=64,
        steps=40,
        cfg_scale=7.0
    )
    
    # SHIELD ICON
    ag.generate_image(
        prompt=("small flat icon of medieval shield, "
                "gold outline, simple design, game UI element, "
                "transparent background, 64x64 pixels"),
        out_path="assets/ui/icon_shield.png",
        width=64,
        height=64,
        steps=40,
        cfg_scale=7.0
    )
    
    print("\n🃏 Generating card frame...")
    # CARD FRAME
    ag.generate_image(
        prompt=("aging parchment card frame with gold filigree border, "
                "ornate medieval design, transparent center window, "
                "512x768 aspect ratio, high quality texture"),
        out_path="assets/ui/card_frame.png",
        width=512,
        height=768,
        steps=60,
        cfg_scale=8.0
    )
    
    print("\n✔️  All new assets generated successfully!")


def main():
    """Main entry point."""
    print("🎮 Medieval Deck - AI Asset Generator")
    print("=" * 50)
    
    try:
        # Step 1: Clean old assets
        clean_legacy_assets()
        
        # Step 2: Generate new assets
        generate_all_assets()
        
        print("\n🎉 Asset generation complete!")
        print("\nNext steps:")
        print("  1. Run: pytest -q")
        print("  2. Run: python src/main.py --skip-select")
        print("  3. Test the new combat corridor!")
        
    except Exception as e:
        print(f"\n❌ Error during asset generation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
