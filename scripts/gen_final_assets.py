#!/usr/bin/env python3
"""
Script para gerar assets IA do layout definitivo
"""

import sys
import logging
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from generators.asset_generator import AssetGenerator
from utils.config import Config

def generate_final_assets():
    """Gera todos os assets do layout definitivo."""
    
    print("🎨 Gerando assets do layout definitivo...")
    
    # Initialize config and generator
    config = Config()
    generator = AssetGenerator(config=config)
    
    assets_dir = Path("assets")
    generated_dir = assets_dir / "generated"
    ui_dir = assets_dir / "ui"
    sheets_dir = assets_dir / "sheets"
    bg_dir = assets_dir / "bg"
    
    # Create directories
    for directory in [generated_dir, ui_dir, sheets_dir, bg_dir]:
        directory.mkdir(exist_ok=True)
    
    print("📁 Diretórios criados")
    
    # === 1. BACKGROUND CORREDOR ===
    print("🏛️ Gerando background do corredor...")
    try:
        generator.generate_background(
            prompt=("medieval cathedral hallway stone floor perspective, "
                   "soft torchlight, parchment texture, semi-realistic, ultrawide, "
                   "dramatic lighting, gothic architecture"),
            output_path=str(generated_dir / "combat_corridor.png"),
            width=3440, height=1440
        )
        print("✅ Background do corredor gerado")
    except Exception as e:
        print(f"❌ Erro ao gerar background: {e}")
    
    # === 2. CARD FRAME PERGAMINHO ===
    print("📜 Gerando frame de carta pergaminho...")
    try:
        generator.generate_ui_element(
            prompt=("ornate parchment card frame, gold filigree border, "
                   "transparent center, medieval scroll, symmetrical, high quality"),
            output_path=str(ui_dir / "card_frame.png"),
            width=512, height=768
        )
        print("✅ Frame de carta gerado")
    except Exception as e:
        print(f"❌ Erro ao gerar frame: {e}")
    
    # === 3. INTENT ICONS ===
    print("⚔️ Gerando ícones de intent...")
    try:
        # Sword icon
        generator.generate_ui_element(
            prompt="flat icon medieval sword gold outline transparent background",
            output_path=str(ui_dir / "icon_sword.png"),
            width=64, height=64
        )
        
        # Shield icon
        generator.generate_ui_element(
            prompt="flat icon medieval shield gold outline transparent background",
            output_path=str(ui_dir / "icon_shield.png"),
            width=64, height=64
        )
        print("✅ Ícones de intent gerados")
    except Exception as e:
        print(f"❌ Erro ao gerar ícones: {e}")
    
    # === 4. SPRITE SHEETS (se o gerador suportar) ===
    print("🎭 Tentando gerar sprite sheets...")
    
    sprite_configs = [
        {
            "name": "knight_idle",
            "prompt": "valiant knight gold armor idle breathing animation",
            "frames": 10,
            "height": 512
        },
        {
            "name": "knight_attack", 
            "prompt": "valiant knight gold armor sword slash attack",
            "frames": 10,
            "height": 512
        },
        {
            "name": "goblin_idle",
            "prompt": "goblin scout leather armor idle sneer animation",
            "frames": 10, 
            "height": 420
        },
        {
            "name": "goblin_attack",
            "prompt": "goblin scout leather armor stab attack animation",
            "frames": 10,
            "height": 420
        }
    ]
    
    for sprite_config in sprite_configs:
        try:
            if hasattr(generator, 'generate_sprite_sheet'):
                generator.generate_sprite_sheet(
                    prompt=sprite_config["prompt"],
                    frame_count=sprite_config["frames"],
                    output_path=str(sheets_dir / f"{sprite_config['name']}.png"),
                    height=sprite_config["height"]
                )
                print(f"✅ Sprite sheet {sprite_config['name']} gerado")
            else:
                print(f"⚠️  Sprite sheets não suportados, usando fallback para {sprite_config['name']}")
                # Generate single sprite as fallback
                generator.generate_ui_element(
                    prompt=sprite_config["prompt"],
                    output_path=str(generated_dir / f"{sprite_config['name']}_sprite.png"),
                    width=256, height=sprite_config["height"]
                )
        except Exception as e:
            print(f"❌ Erro ao gerar sprite {sprite_config['name']}: {e}")
    
    print("🎉 Geração de assets concluída!")
    print("\n📋 Assets gerados:")
    print(f"  🏛️ {generated_dir / 'combat_corridor.png'}")
    print(f"  📜 {ui_dir / 'card_frame.png'}")
    print(f"  ⚔️ {ui_dir / 'icon_sword.png'}")
    print(f"  🛡️ {ui_dir / 'icon_shield.png'}")
    print(f"  🎭 Sprite sheets em {sheets_dir}")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        generate_final_assets()
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)
