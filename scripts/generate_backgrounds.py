#!/usr/bin/env python3
"""
Medieval Deck - Script de Geração de Backgrounds Consistentes

Regenera todos os backgrounds do jogo com estilo visual unificado.
"""

import sys
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generators.asset_generator import AssetGenerator
from models.sdxl_pipeline import SDXLPipeline

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Gera backgrounds consistentes para todas as telas do jogo."""
    
    # Configuração dos backgrounds
    backgrounds = {
        "main_menu_bg": {
            "prompt": "epic medieval castle courtyard at sunset, grand stone architecture with banners, warm golden lighting, atmospheric fog, masterpiece, high quality, detailed, medieval fantasy, gothic architecture, dramatic lighting, 3440x1440 ultrawide aspect ratio",
            "size": (3440, 1440),
            "description": "Background principal do menu"
        },
        "character_selection_bg": {
            "prompt": "medieval tavern interior with warm fireplace, wooden tables and chairs, hanging lanterns, cozy atmosphere, detailed textures, masterpiece, high quality, medieval fantasy, warm lighting, atmospheric, 3440x1440 ultrawide aspect ratio",
            "size": (3440, 1440),
            "description": "Background da seleção de personagem"
        },
        "combat_bg": {
            "prompt": "epic medieval battlefield with ancient ruins, dramatic storm clouds, lightning in distance, gothic stone architecture, atmospheric mist, masterpiece, high quality, detailed, medieval fantasy, dramatic lighting, cinematic, 3440x1440 ultrawide aspect ratio",
            "size": (3440, 1440),
            "description": "Background de combate"
        },
        "victory_bg": {
            "prompt": "triumphant medieval castle with golden sunlight, victory banners waving, peaceful countryside, bright warm lighting, celebratory atmosphere, masterpiece, high quality, detailed, medieval fantasy, golden hour lighting, 3440x1440 ultrawide aspect ratio",
            "size": (3440, 1440),
            "description": "Background de vitória"
        },
        "defeat_bg": {
            "prompt": "dark medieval graveyard at night, ominous fog, dead trees, moonlight through clouds, somber atmosphere, detailed stone tombstones, masterpiece, high quality, detailed, medieval fantasy, dark moody lighting, 3440x1440 ultrawide aspect ratio",
            "size": (3440, 1440),
            "description": "Background de derrota"
        }
    }
    
    try:
        # Inicializar pipeline SDXL
        logger.info("Inicializando pipeline SDXL...")
        pipeline = SDXLPipeline()
        
        if not pipeline.initialize():
            logger.error("Falha ao inicializar pipeline SDXL")
            return False
            
        # Inicializar gerador de assets
        generator = AssetGenerator(pipeline)
        
        # Gerar cada background
        total_generated = 0
        total_failed = 0
        
        for bg_id, config in backgrounds.items():
            logger.info(f"\n🎨 Gerando: {config['description']}")
            logger.info(f"Prompt: {config['prompt']}")
            
            try:
                # Gerar background em alta resolução
                result = generator.generate_asset(
                    prompt=config["prompt"],
                    asset_type="background",
                    asset_id=bg_id,
                    width=config["size"][0],
                    height=config["size"][1],
                    num_inference_steps=80,
                    guidance_scale=8.5
                )
                
                if result:
                    total_generated += 1
                    logger.info(f"✅ {bg_id} gerado com sucesso: {result}")
                else:
                    total_failed += 1
                    logger.error(f"❌ Falha ao gerar {bg_id}")
                    
            except Exception as e:
                total_failed += 1
                logger.error(f"❌ Erro ao gerar {bg_id}: {e}")
                
        # Gerar versões redimensionadas para diferentes resoluções
        logger.info(f"\n📐 Gerando versões redimensionadas...")
        
        resolutions = [
            (1920, 1080),  # Full HD
            (2560, 1440),  # QHD
            (1366, 768),   # HD
            (1024, 768)    # Fallback
        ]
        
        # Redimensionar cada background gerado
        for bg_id in backgrounds.keys():
            for width, height in resolutions:
                try:
                    result = generator.resize_asset(
                        asset_id=bg_id,
                        new_width=width,
                        new_height=height,
                        suffix=f"_{width}x{height}"
                    )
                    if result:
                        logger.debug(f"✅ {bg_id} redimensionado para {width}x{height}")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao redimensionar {bg_id} para {width}x{height}: {e}")
        
        # Resumo final
        logger.info(f"\n🎯 RESUMO FINAL:")
        logger.info(f"   Backgrounds gerados: {total_generated}/{len(backgrounds)}")
        logger.info(f"   Falhas: {total_failed}")
        logger.info(f"   Taxa de sucesso: {total_generated/(total_generated+total_failed)*100:.1f}%" if (total_generated+total_failed) > 0 else "N/A")
        
        if total_generated > 0:
            logger.info(f"\n✅ Backgrounds salvos em: assets/generated/")
            logger.info(f"📁 Múltiplas resoluções disponíveis!")
            logger.info(f"🎮 Execute o jogo para ver os novos backgrounds!")
            return True
        else:
            logger.error(f"\n❌ Nenhum background foi gerado com sucesso")
            return False
            
    except Exception as e:
        logger.error(f"Erro durante geração: {e}", exc_info=True)
        return False
        
    finally:
        # Cleanup GPU memory
        if 'pipeline' in locals():
            pipeline.cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
