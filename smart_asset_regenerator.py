#!/usr/bin/env python3
"""
Script inteligente para regenerar apenas assets que estão faltando ou com problemas.
Verifica a qualidade e existência dos arquivos antes de regenerar.
"""

import logging
import os
from pathlib import Path
import sys
from PIL import Image
import hashlib

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.utils.config import Config
from src.models.sdxl_pipeline import SDXLPipeline
from src.generators.asset_generator import AssetGenerator

def setup_logging():
    """Configura logging sem emojis para evitar problemas de encoding."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('smart_asset_check.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def check_image_quality(image_path: Path) -> dict:
    """
    Verifica a qualidade de uma imagem e retorna informações sobre ela.
    
    Returns:
        dict: Informações sobre a imagem (size, format, quality_score, etc.)
    """
    if not image_path.exists():
        return {"exists": False, "needs_regeneration": True, "reason": "File not found"}
    
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            file_size = image_path.stat().st_size
            format_type = img.format
            
            # Calcular score de qualidade baseado em tamanho e resolução
            expected_min_size = 1024 * 1024  # 1MB mínimo
            expected_resolution = 3440 * 1440  # Resolução esperada
            current_resolution = width * height
            
            quality_issues = []
            
            # Verificar resolução
            if current_resolution < expected_resolution * 0.8:  # 80% da resolução esperada
                quality_issues.append(f"Low resolution: {width}x{height}")
            
            # Verificar tamanho do arquivo
            if file_size < expected_min_size:
                quality_issues.append(f"Small file size: {file_size/1024/1024:.1f}MB")
            
            # Verificar formato
            if format_type not in ['PNG', 'JPEG']:
                quality_issues.append(f"Unexpected format: {format_type}")
            
            # Verificar se é muito pequeno (possível erro de geração)
            if file_size < 500 * 1024:  # Menor que 500KB é suspeito
                quality_issues.append("Suspiciously small file size")
            
            needs_regen = len(quality_issues) > 0
            
            return {
                "exists": True,
                "width": width,
                "height": height,
                "file_size_mb": file_size / 1024 / 1024,
                "format": format_type,
                "quality_issues": quality_issues,
                "needs_regeneration": needs_regen,
                "reason": "; ".join(quality_issues) if quality_issues else "Good quality"
            }
            
    except Exception as e:
        return {
            "exists": True,
            "needs_regeneration": True,
            "reason": f"Error reading image: {str(e)}"
        }

def check_all_assets(config: Config) -> dict:
    """
    Verifica todos os assets necessários e retorna um relatório.
    
    Returns:
        dict: Relatório de todos os assets
    """
    logger = logging.getLogger(__name__)
    
    # Assets que precisam existir
    required_assets = {
        # Backgrounds dos personagens
        "character_backgrounds": {
            "knight_bg.png": "Knight character background",
            "wizard_bg.png": "Wizard character background", 
            "assassin_bg.png": "Assassin character background"
        },
        
        # Sprites transparentes dos personagens
        "character_sprites": {
            "knight_transparent.png": "Knight transparent sprite",
            "wizard_transparent.png": "Wizard transparent sprite",
            "assassin_transparent.png": "Assassin transparent sprite"
        },
        
        # Backgrounds de combate
        "combat_backgrounds": {
            "combat_bg_goblin_cave.png": "Goblin combat background",
            "combat_bg_orc_camp.png": "Orc combat background", 
            "combat_bg_skeleton_crypt.png": "Skeleton combat background",
            "combat_bg_dragon_lair.png": "Dragon combat background",
            "combat_bg_dark_tower.png": "Dark mage combat background"
        },
        
        # Sprites de inimigos melhorados
        "enemy_sprites": {
            "goblin_sprite_enhanced.png": "Enhanced goblin sprite",
            "orc_sprite_enhanced.png": "Enhanced orc sprite",
            "skeleton_sprite_enhanced.png": "Enhanced skeleton sprite", 
            "dragon_sprite_enhanced.png": "Enhanced dragon sprite",
            "dark_mage_sprite_enhanced.png": "Enhanced dark mage sprite"
        },
        
        # Sprites de personagens melhorados
        "enhanced_character_sprites": {
            "knight_sprite_enhanced.png": "Enhanced knight sprite",
            "wizard_sprite_enhanced.png": "Enhanced wizard sprite",
            "assassin_sprite_enhanced.png": "Enhanced assassin sprite"
        }
    }
    
    report = {}
    assets_to_regenerate = []
    
    logger.info("Checking all required assets...")
    
    for category, assets in required_assets.items():
        logger.info(f"Checking category: {category}")
        report[category] = {}
        
        for filename, description in assets.items():
            asset_path = config.assets_generated_dir / filename
            check_result = check_image_quality(asset_path)
            check_result["description"] = description
            
            report[category][filename] = check_result
            
            if check_result["needs_regeneration"]:
                assets_to_regenerate.append({
                    "category": category,
                    "filename": filename,
                    "description": description,
                    "reason": check_result["reason"]
                })
                logger.warning(f"NEEDS REGEN: {filename} - {check_result['reason']}")
            else:
                logger.info(f"OK: {filename}")
    
    report["summary"] = {
        "total_assets": sum(len(assets) for assets in required_assets.values()),
        "assets_needing_regeneration": len(assets_to_regenerate),
        "assets_to_regenerate": assets_to_regenerate
    }
    
    return report

def regenerate_missing_assets(config: Config, report: dict) -> bool:
    """
    Regenera apenas os assets que estão faltando ou com problemas.
    
    Args:
        config: Configuration object
        report: Relatório dos assets
        
    Returns:
        bool: True se todos os assets foram regenerados com sucesso
    """
    logger = logging.getLogger(__name__)
    
    assets_to_regen = report["summary"]["assets_to_regenerate"]
    
    if not assets_to_regen:
        logger.info("All assets are good! No regeneration needed.")
        return True
        
    logger.info(f"Regenerating {len(assets_to_regen)} assets...")
    
    # Initialize SDXL pipeline only if needed
    pipeline = None
    asset_generator = None
    
    try:
        logger.info("Initializing SDXL pipeline...")
        pipeline = SDXLPipeline(
            model_id="stabilityai/stable-diffusion-xl-base-1.0",
            refiner_id="stabilityai/stable-diffusion-xl-refiner-1.0",
            enable_refiner=True,
            device="cuda",
            cache_dir=str(config.assets_cache_dir),
            memory_efficient=True
        )
        
        logger.info("Initializing asset generator...")
        asset_generator = AssetGenerator(
            config=config,
            sdxl_pipeline=pipeline,
            cache_dir=str(config.assets_cache_dir)
        )
        
        success_count = 0
        
        for asset_info in assets_to_regen:
            category = asset_info["category"]
            filename = asset_info["filename"]
            description = asset_info["description"]
            
            logger.info(f"Regenerating: {filename} ({description})")
            
            try:
                # Regenerar baseado na categoria
                if category == "character_backgrounds":
                    success = regenerate_character_background(asset_generator, filename)
                elif category == "character_sprites":
                    success = regenerate_character_sprite(asset_generator, filename)
                elif category == "combat_backgrounds":
                    success = regenerate_combat_background(asset_generator, filename)
                elif category in ["enemy_sprites", "enhanced_character_sprites"]:
                    success = regenerate_enhanced_sprite(asset_generator, filename)
                else:
                    logger.warning(f"Unknown category: {category}")
                    success = False
                
                if success:
                    success_count += 1
                    logger.info(f"SUCCESS: {filename} regenerated")
                else:
                    logger.error(f"FAILED: {filename} regeneration failed")
                    
            except Exception as e:
                logger.error(f"ERROR regenerating {filename}: {e}")
        
        logger.info(f"Regeneration complete: {success_count}/{len(assets_to_regen)} successful")
        return success_count == len(assets_to_regen)
        
    except Exception as e:
        logger.error(f"Error during regeneration: {e}")
        return False
        
    finally:
        if pipeline:
            pipeline.unload_models()
            logger.info("Pipeline unloaded")

def regenerate_character_background(asset_generator: AssetGenerator, filename: str) -> bool:
    """Regenera background de personagem específico."""
    logger = logging.getLogger(__name__)
    
    character_prompts = {
        "knight_bg.png": {
            "prompt": "epic medieval castle throne room, golden ornate interior, royal banners, stained glass windows, warm lighting, no people, empty majestic hall",
            "negative": "people, characters, figures, dark, blurry, low quality"
        },
        "wizard_bg.png": {
            "prompt": "mystical wizard tower library, floating books, glowing runes, magical artifacts, purple blue lighting, ancient scrolls, no people",
            "negative": "people, characters, figures, dark, blurry, low quality"
        },
        "assassin_bg.png": {
            "prompt": "dark medieval city rooftops at night, moonlight shadows, stone buildings, mysterious atmosphere, no people, empty streets",
            "negative": "people, characters, figures, bright, blurry, low quality"
        }
    }
    
    if filename not in character_prompts:
        logger.error(f"No prompt defined for {filename}")
        return False
    
    prompt_data = character_prompts[filename]
    
    try:
        # Use the existing character background generation method
        results = asset_generator.generate_character_backgrounds(force_regenerate=True)
        
        # Check if our specific file was generated
        character_id = filename.replace("_bg.png", "")
        return character_id in results
        
    except Exception as e:
        logger.error(f"Error generating character background {filename}: {e}")
        return False

def regenerate_character_sprite(asset_generator: AssetGenerator, filename: str) -> bool:
    """Regenera sprite transparente de personagem específico."""
    try:
        results = asset_generator.generate_transparent_character_sprites(force_regenerate=True)
        character_id = filename.replace("_transparent.png", "")
        return f"{character_id}_transparent" in results
    except Exception as e:
        logging.getLogger(__name__).error(f"Error generating character sprite {filename}: {e}")
        return False

def regenerate_combat_background(asset_generator: AssetGenerator, filename: str) -> bool:
    """Regenera background de combate específico."""
    try:
        results = asset_generator.generate_enemy_backgrounds(force_regenerate=True)
        return filename in [Path(path).name for path in results.values()]
    except Exception as e:
        logging.getLogger(__name__).error(f"Error generating combat background {filename}: {e}")
        return False

def regenerate_enhanced_sprite(asset_generator: AssetGenerator, filename: str) -> bool:
    """Regenera sprite melhorado específico."""
    try:
        results = asset_generator.generate_enhanced_sprites(force_regenerate=True)
        return filename in [Path(path).name for path in results.values()]
    except Exception as e:
        logging.getLogger(__name__).error(f"Error generating enhanced sprite {filename}: {e}")
        return False

def main():
    """Função principal que executa a verificação e regeneração inteligente."""
    logger = setup_logging()
    
    logger.info("Starting smart asset checker and regenerator...")
    
    try:
        # Initialize config
        config = Config()
        
        # Check all assets
        logger.info("Scanning all required assets...")
        report = check_all_assets(config)
        
        # Print summary
        summary = report["summary"]
        logger.info(f"Asset check complete:")
        logger.info(f"  Total assets: {summary['total_assets']}")
        logger.info(f"  Assets needing regeneration: {summary['assets_needing_regeneration']}")
        
        if summary['assets_needing_regeneration'] == 0:
            logger.info("All assets are good! No work needed.")
            return True
        
        # Show what needs to be regenerated
        logger.info("Assets that need regeneration:")
        for asset in summary['assets_to_regenerate']:
            logger.info(f"  - {asset['filename']}: {asset['reason']}")
        
        # Ask for confirmation (or auto-proceed)
        logger.info("Starting regeneration of missing/problematic assets...")
        
        # Regenerate missing assets
        success = regenerate_missing_assets(config, report)
        
        if success:
            logger.info("All missing assets regenerated successfully!")
            return True
        else:
            logger.error("Some assets failed to regenerate")
            return False
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("SUCCESS: Asset check and regeneration completed!")
    else:
        print("FAILED: Some issues occurred during asset regeneration")
