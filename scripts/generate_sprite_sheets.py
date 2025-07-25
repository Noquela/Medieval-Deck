#!/usr/bin/env python3
"""
Medieval Deck - Script de Geração de Sprite Sheets

Gera automaticamente todas as animações de personagens usando IA.
Execute este script para criar sprite sheets 30fps para todos os personagens.
"""

import sys
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from generators.sprite_sheet_generator import SpriteSheetGenerator
    from models.sdxl_pipeline import SDXLPipeline
except ImportError as e:
    print(f"Erro de import: {e}")
    print("Tentando import direto...")
    # Fallback para import direto
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.generators.sprite_sheet_generator import SpriteSheetGenerator

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Gera sprite sheets para todos os personagens do jogo."""
    
    # Configuração dos personagens com prompts consistentes
    characters = {
        "knight": {
            "prompt": "heroic medieval knight in full plate armor, noble warrior with silver armor and blue cape, holding longsword and shield, masterpiece, high quality, detailed armor, medieval fantasy style, consistent character design",
            "actions": ["idle", "attack", "cast", "hurt"]
        },
        "goblin": {
            "prompt": "vicious green goblin warrior with crude weapons, snarling creature with pointed ears and yellow eyes, torn leather armor, masterpiece, high quality, detailed, medieval fantasy style, consistent character design",
            "actions": ["idle", "attack", "hurt", "death"]
        },
        "orc": {
            "prompt": "massive green orc berserker with battle axe, fierce barbaric warrior with tusks and muscular build, dark leather and metal armor, masterpiece, high quality, detailed, medieval fantasy style, consistent character design",
            "actions": ["idle", "attack", "hurt", "death"]
        },
        "skeleton": {
            "prompt": "undead skeleton archer with bone bow, ancient warrior risen from grave, tattered robes and exposed bones, glowing eye sockets, masterpiece, high quality, detailed, medieval fantasy style, consistent character design",
            "actions": ["idle", "attack", "hurt", "death"]
        },
        "mage": {
            "prompt": "dark mage with mystical purple robes and wooden staff, wielder of forbidden magic, hooded figure with glowing magical aura, masterpiece, high quality, detailed, medieval fantasy style, consistent character design",
            "actions": ["idle", "attack", "cast", "hurt", "death"]
        },
        "dragon": {
            "prompt": "ancient red dragon breathing fire, massive legendary beast with scaled hide and powerful wings, golden eyes and sharp claws, masterpiece, high quality, detailed, medieval fantasy style, consistent character design",
            "actions": ["idle", "attack", "hurt", "death"]
        }
    }
    
    try:
        # Inicializar pipeline SDXL
        logger.info("Inicializando pipeline SDXL...")
        pipeline = SDXLPipeline()
        
        if not pipeline.initialize():
            logger.error("Falha ao inicializar pipeline SDXL")
            return False
            
        # Inicializar gerador de sprite sheets
        generator = SpriteSheetGenerator(pipeline)
        
        # Gerar animações para cada personagem
        total_generated = 0
        total_failed = 0
        
        for char_id, config in characters.items():
            logger.info(f"\n🎨 Gerando animações para: {char_id}")
            logger.info(f"Prompt base: {config['prompt']}")
            
            # Gerar todas as animações do personagem
            results = generator.generate_character_animations(
                char_id=char_id,
                base_prompt=config["prompt"],
                actions=config["actions"]
            )
            
            # Contar resultados
            success_count = len(results)
            failed_count = len(config["actions"]) - success_count
            
            total_generated += success_count
            total_failed += failed_count
            
            logger.info(f"✅ {char_id}: {success_count} animações geradas, {failed_count} falharam")
            
            # Listar arquivos gerados
            for action, path in results.items():
                logger.info(f"   - {action}: {path}")
                
        # Resumo final
        logger.info(f"\n🎯 RESUMO FINAL:")
        logger.info(f"   Total gerado: {total_generated} sprite sheets")
        logger.info(f"   Total falhado: {total_failed}")
        logger.info(f"   Taxa de sucesso: {total_generated/(total_generated+total_failed)*100:.1f}%")
        
        if total_generated > 0:
            logger.info(f"\n✅ Sprite sheets salvos em: assets/sprite_sheets/")
            logger.info(f"📁 Execute o jogo para ver as animações 30fps!")
            return True
        else:
            logger.error(f"\n❌ Nenhum sprite sheet foi gerado com sucesso")
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
