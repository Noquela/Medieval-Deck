#!/usr/bin/env python3
"""
Medieval Deck - MVP Asset Generation

Gera assets básicos para o MVP:
- 2 biomas (Catedral Nobre + Caverna Goblin)
- 1 herói (Cavaleiro com idle/attack)
- 2 inimigos (Goblin Scout + Skeleton Warrior com idle/attack)
- UI elementos (card frame, botões)
"""

import sys
import logging
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.generators.asset_generator import AssetGenerator
from src.models.sdxl_pipeline import SDXLPipeline
from src.models.card_models import Card, CardType, Rarity

def setup_logging():
    """Setup logging for asset generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('mvp_asset_generation.log')
        ]
    )
    return logging.getLogger(__name__)

def generate_backgrounds(asset_generator, logger):
    """Generate the 2 MVP biomes."""
    logger.info("Generating MVP Backgrounds...")
    
    backgrounds = {
        "cathedral": {
            "prompt": "medieval cathedral interior, stone arches, stained glass, altar, dramatic lighting",
            "path": "bg/cathedral.png"
        },
        "goblin_cave": {
            "prompt": "goblin cave, rough stone walls, campfire glow, mushrooms, tribal decorations",
            "path": "bg/goblin_cave.png"
        }
    }
    
    results = {}
    for bg_id, bg_data in backgrounds.items():
        logger.info(f"Generating {bg_id}...")
        try:
            # Criar um Card mock para usar com o método
            mock_card = Card(
                id=f"bg_{bg_id}",
                name=bg_id.replace("_", " ").title(),
                type=CardType.LAND,
                cost=0,
                rarity=Rarity.COMMON,
                background_prompt=bg_data["prompt"]
            )
            
            # Usar método disponível no AssetGenerator com prompt direto
            # Bypass do optimizer para manter prompts curtos
            image = asset_generator.sdxl_pipeline.generate_image(
                prompt=bg_data["prompt"],
                num_inference_steps=80,
                guidance_scale=8.5,
                width=1024,
                height=1024
            )
            
            # Salvar manualmente
            bg_path = asset_generator.generated_dir / bg_data["path"]
            bg_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(bg_path, "PNG", quality=95)
            
            results[bg_id] = str(bg_path)
            logger.info(f"Generated {bg_id}: {results[bg_id]}")
        except Exception as e:
            logger.error(f"Error generating {bg_id}: {e}")
            results[bg_id] = None
    
    return results

def generate_sprite_sheets(asset_generator, logger):
    """Generate sprite sheets for hero and enemies."""
    logger.info("Generating MVP Sprite Sheets...")
    
    # Mapear personagens MVP para nomes reconhecidos
    character_mapping = {
        "knight": "Cavaleiro Valente",
        "goblin": "Goblin Scout",  # Vou adicionar suporte
        "skeleton": "Skeleton Warrior"  # Vou adicionar suporte
    }
    
    results = {}
    for char_id, char_name in character_mapping.items():
        logger.info(f"Generating {char_id}...")
        try:
            # Usar método disponível - gerar sprite individual
            result = asset_generator.generate_character_sprite(
                character_name=char_name,
                force_regenerate=True
            )
            if result:
                results[char_id] = result
                logger.info(f"Generated {char_id}: {result}")
            else:
                logger.error(f"Failed to generate {char_id}")
        except Exception as e:
            logger.error(f"Error generating {char_id}: {e}")
    
    return results

def generate_ui_elements(asset_generator, logger):
    """Generate UI elements."""
    logger.info("Generating MVP UI Elements...")
    
    # Usar método disponível
    try:
        results = asset_generator.generate_ui_assets(force_regenerate=True)
        
        if results:
            logger.info(f"Generated {len(results)} UI elements")
            for ui_id, path in results.items():
                logger.info(f"Generated {ui_id}: {path}")
        else:
            logger.error("Failed to generate UI elements")
        
        return results
        
    except Exception as e:
        logger.error(f"Error generating UI elements: {e}")
        return {}

def main():
    """Main MVP asset generation."""
    logger = setup_logging()
    logger.info("Starting Medieval Deck MVP Asset Generation...")
    
    try:
        # Initialize configuration and AI pipeline
        config = Config()
        
        # Initialize SDXL pipeline
        pipeline = SDXLPipeline(
            model_id=config.ai.model_id,
            refiner_id=config.ai.refiner_id,
            enable_refiner=config.ai.enable_refiner,
            device=config.get_device(),
            cache_dir=str(config.assets_cache_dir),
            memory_efficient=config.ai.memory_efficient
        )
        
        # Initialize asset generator
        asset_generator = AssetGenerator(
            config=config,
            sdxl_pipeline=pipeline,
            cache_dir=str(config.assets_cache_dir)
        )
        
        # Create directories
        (project_root / "assets" / "bg").mkdir(parents=True, exist_ok=True)
        (project_root / "assets" / "sheets").mkdir(parents=True, exist_ok=True)
        (project_root / "assets" / "ui").mkdir(parents=True, exist_ok=True)
        
        # Generate all MVP assets
        bg_results = generate_backgrounds(asset_generator, logger)
        sprite_results = generate_sprite_sheets(asset_generator, logger)
        ui_results = generate_ui_elements(asset_generator, logger)
        
        # Summary
        total_backgrounds = len([r for r in bg_results.values() if r is not None])
        total_sprites = len([r for r in sprite_results.values() if r is not None])
        total_ui = len([r for r in ui_results.values() if r is not None])
        total_assets = total_backgrounds + total_sprites + total_ui
        
        logger.info(f"MVP Asset Generation Complete!")
        logger.info(f"Generated {total_assets} assets:")
        logger.info(f"   • {total_backgrounds} backgrounds")
        logger.info(f"   • {total_sprites} sprite sheets")
        logger.info(f"   • {total_ui} UI elements")
        
        if total_assets > 0:
            logger.info("Ready for MVP implementation!")
            return True
        else:
            logger.error("No assets were generated")
            return False
            
    except Exception as e:
        logger.error(f"Fatal error during MVP asset generation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
