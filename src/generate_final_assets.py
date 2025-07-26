#!/usr/bin/env python3
"""
Script para gerar assets finais do layout definitivo Stage-Action.
"""

import logging
from generators.asset_generator import AssetGenerator
from utils.config import Config

def generate_corridor_background():
    """Gera background de corredor medieval."""
    try:
        generator = AssetGenerator()
        
        prompt = """medieval stone corridor, gothic arches, torches on walls, 
        atmospheric lighting, dark stone floor, perspective view, 
        masterpiece, high quality, detailed architecture, dramatic shadows"""
        
        negative_prompt = """modern, bright, colorful, cartoon, low quality, 
        blurry, text, watermark"""
        
        print("🏰 Generating corridor background...")
        
        # Generate corridor background (1400x800 for stage area)
        background = generator.generate_background(
            prompt=prompt,
            negative_prompt=negative_prompt,
            filename="corridor_stage_bg",
            size=(1400, 800)
        )
        
        if background:
            print("✅ Corridor background generated successfully!")
            return True
        else:
            print("❌ Failed to generate corridor background")
            return False
            
    except Exception as e:
        print(f"❌ Error generating corridor: {e}")
        return False

def generate_card_frames():
    """Gera frames ornamentados para cartas."""
    try:
        generator = AssetGenerator()
        
        frame_types = [
            ("attack", "ornate golden frame, medieval manuscript style, red gems"),
            ("defense", "silver frame with blue crystals, protective runes"),
            ("magic", "mystical purple frame, arcane symbols, glowing edges"),
            ("generic", "bronze frame, simple medieval border, parchment style")
        ]
        
        print("🎴 Generating card frames...")
        
        for frame_type, description in frame_types:
            prompt = f"""medieval card frame, {description}, 
            ornate border, detailed metalwork, masterpiece, high quality, 
            transparent center, decorative corners"""
            
            negative_prompt = """filled center, opaque, modern, plastic, 
            low quality, blurry"""
            
            frame = generator.generate_ui_element(
                prompt=prompt,
                negative_prompt=negative_prompt,
                filename=f"card_frame_{frame_type}",
                size=(180, 270)  # Theme.CARD_SIZE
            )
            
            if frame:
                print(f"✅ {frame_type} frame generated!")
            else:
                print(f"❌ Failed to generate {frame_type} frame")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating frames: {e}")
        return False

def generate_intent_icons():
    """Gera ícones de intenção do inimigo."""
    try:
        generator = AssetGenerator()
        
        icons = [
            ("attack", "medieval sword icon, red glow, sharp blade"),
            ("block", "medieval shield icon, blue glow, defensive stance"),
            ("special", "mystical spell icon, purple energy, magic runes")
        ]
        
        print("🎯 Generating intent icons...")
        
        for icon_type, description in icons:
            prompt = f"""medieval {description}, simple icon design, 
            clear symbol, high contrast, masterpiece, detailed"""
            
            negative_prompt = """complex background, cluttered, modern, 
            low quality, blurry"""
            
            icon = generator.generate_ui_element(
                prompt=prompt,
                negative_prompt=negative_prompt,
                filename=f"intent_icon_{icon_type}",
                size=(64, 64)
            )
            
            if icon:
                print(f"✅ {icon_type} icon generated!")
            else:
                print(f"❌ Failed to generate {icon_type} icon")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating icons: {e}")
        return False

def main():
    """Main function."""
    print("🎨 Starting final asset generation for Stage-Action layout...")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    success_count = 0
    total_tasks = 3
    
    # Generate corridor background
    if generate_corridor_background():
        success_count += 1
    
    print("-" * 40)
    
    # Generate card frames
    if generate_card_frames():
        success_count += 1
    
    print("-" * 40)
    
    # Generate intent icons
    if generate_intent_icons():
        success_count += 1
    
    print("=" * 60)
    print(f"🎯 Asset generation complete: {success_count}/{total_tasks} tasks successful")
    
    if success_count == total_tasks:
        print("🎉 All assets generated successfully!")
        print("📁 Check assets/generated/ for new files")
    else:
        print("⚠️ Some assets failed to generate. Check logs for details.")
    
    return success_count == total_tasks

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
