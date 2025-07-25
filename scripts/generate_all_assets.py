#!/usr/bin/env python3
"""
Medieval Deck - Geração Completa de Assets

Script principal que gera TODOS os assets do jogo com consistência visual:
- Backgrounds de todas as telas
- Sprite sheets de animação 30fps
- Assets de UI e botões
"""

import sys
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.sdxl_pipeline import SDXLPipeline
from generators.asset_generator import AssetGenerator
from generators.sprite_sheet_generator import SpriteSheetGenerator

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MedievalAssetGenerator:
    """Gerador principal de todos os assets do Medieval Deck."""
    
    def __init__(self):
        self.pipeline = None
        self.asset_generator = None
        self.sprite_generator = None
        
    def initialize(self):
        """Inicializa todos os geradores."""
        try:
            logger.info("🚀 Inicializando pipeline SDXL...")
            self.pipeline = SDXLPipeline()
            
            if not self.pipeline.initialize():
                logger.error("❌ Falha ao inicializar pipeline SDXL")
                return False
                
            self.asset_generator = AssetGenerator(self.pipeline)
            self.sprite_generator = SpriteSheetGenerator(self.pipeline)
            
            logger.info("✅ Pipeline inicializado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar: {e}")
            return False
    
    def generate_backgrounds(self):
        """Gera todos os backgrounds do jogo."""
        logger.info("\n🏰 === GERANDO BACKGROUNDS ===")
        
        backgrounds = {
            "main_menu_bg": {
                "prompt": "epic medieval castle courtyard at sunset, grand stone architecture with heraldic banners, warm golden lighting, atmospheric fog, masterpiece, high quality, detailed textures, medieval fantasy, gothic architecture, dramatic lighting, cinematic composition",
                "description": "Menu Principal"
            },
            "character_selection_bg": {
                "prompt": "cozy medieval tavern interior with warm fireplace, wooden tables and chairs, hanging lanterns casting warm light, detailed wood textures, stone walls, masterpiece, high quality, medieval fantasy, atmospheric lighting",
                "description": "Seleção de Personagem"
            },
            "combat_bg": {
                "prompt": "epic medieval battlefield with ancient stone ruins, dramatic storm clouds, lightning illuminating gothic architecture, atmospheric mist, battle-worn ground, masterpiece, high quality, detailed, medieval fantasy, dramatic cinematic lighting",
                "description": "Combate"
            },
            "victory_bg": {
                "prompt": "triumphant medieval castle with golden sunlight, victory banners waving in wind, peaceful countryside vista, bright warm lighting, celebratory atmosphere, detailed stone architecture, masterpiece, high quality, medieval fantasy, golden hour",
                "description": "Vitória"
            },
            "defeat_bg": {
                "prompt": "dark medieval graveyard at night, ominous fog rolling through, dead twisted trees, moonlight filtering through storm clouds, weathered stone tombstones, somber atmosphere, masterpiece, high quality, medieval fantasy, moody lighting",
                "description": "Derrota"
            }
        }
        
        success_count = 0
        for bg_id, config in backgrounds.items():
            logger.info(f"🎨 Gerando: {config['description']}")
            
            try:
                result = self.asset_generator.generate_asset(
                    prompt=config["prompt"],
                    asset_type="background",
                    asset_id=bg_id,
                    width=3440,
                    height=1440,
                    num_inference_steps=80,
                    guidance_scale=8.5
                )
                
                if result:
                    success_count += 1
                    logger.info(f"✅ {config['description']} gerado!")
                else:
                    logger.error(f"❌ Falha: {config['description']}")
                    
            except Exception as e:
                logger.error(f"❌ Erro em {config['description']}: {e}")
        
        logger.info(f"🎯 Backgrounds: {success_count}/{len(backgrounds)} gerados")
        return success_count > 0
    
    def generate_character_animations(self):
        """Gera animações 30fps para todos os personagens."""
        logger.info("\n⚔️ === GERANDO ANIMAÇÕES ===")
        
        characters = {
            "knight": {
                "prompt": "heroic medieval knight in full plate armor, noble warrior with silver armor and blue cape, holding longsword and shield, detailed metallic textures, masterpiece, high quality, medieval fantasy style, consistent character design",
                "actions": ["idle", "attack", "cast", "hurt"]
            },
            "goblin": {
                "prompt": "vicious green goblin warrior with crude weapons, snarling creature with pointed ears and yellow eyes, torn leather armor, tribal markings, masterpiece, high quality, medieval fantasy style, consistent character design",
                "actions": ["idle", "attack", "hurt", "death"]
            },
            "orc": {
                "prompt": "massive green orc berserker with battle axe, fierce barbaric warrior with tusks and muscular build, dark leather and metal armor, battle scars, masterpiece, high quality, medieval fantasy style, consistent character design",
                "actions": ["idle", "attack", "hurt", "death"]
            },
            "skeleton": {
                "prompt": "undead skeleton archer with bone bow, ancient warrior risen from grave, tattered dark robes and exposed bones, glowing red eye sockets, masterpiece, high quality, medieval fantasy style, consistent character design",
                "actions": ["idle", "attack", "hurt", "death"]
            },
            "mage": {
                "prompt": "dark mage with mystical purple robes and ornate wooden staff, wielder of forbidden magic, hooded figure with glowing magical aura around hands, masterpiece, high quality, medieval fantasy style, consistent character design",
                "actions": ["idle", "attack", "cast", "hurt", "death"]
            }
        }
        
        total_animations = 0
        success_animations = 0
        
        for char_id, config in characters.items():
            logger.info(f"🧙 Gerando animações: {char_id.title()}")
            
            results = self.sprite_generator.generate_character_animations(
                char_id=char_id,
                base_prompt=config["prompt"],
                actions=config["actions"]
            )
            
            success_animations += len(results)
            total_animations += len(config["actions"])
            
            for action, path in results.items():
                logger.info(f"  ✅ {action}: {Path(path).name}")
        
        logger.info(f"🎯 Animações: {success_animations}/{total_animations} geradas")
        return success_animations > 0
    
    def generate_ui_assets(self):
        """Gera assets de interface."""
        logger.info("\n🎨 === GERANDO UI ASSETS ===")
        
        ui_assets = {
            "button_texture_gold": {
                "prompt": "ornate medieval button texture, golden metallic surface with decorative engravings, detailed craftsmanship, luxury medieval design, seamless texture, high quality",
                "description": "Botão Dourado"
            },
            "button_texture_stone": {
                "prompt": "medieval stone button texture, weathered gray stone with carved details, ancient craftsmanship, seamless texture, high quality",
                "description": "Botão de Pedra"
            },
            "button_texture_mystical": {
                "prompt": "magical medieval button texture, purple mystical energy with glowing runes, arcane symbols, fantasy magic texture, seamless, high quality",
                "description": "Botão Místico"
            },
            "frame_ornate": {
                "prompt": "ornate medieval frame border, golden decorative edges with intricate engravings, royal medieval design, transparent center, detailed craftsmanship, high quality",
                "description": "Moldura Ornamentada"
            }
        }
        
        success_count = 0
        for asset_id, config in ui_assets.items():
            logger.info(f"🎨 Gerando: {config['description']}")
            
            try:
                result = self.asset_generator.generate_asset(
                    prompt=config["prompt"],
                    asset_type="ui",
                    asset_id=asset_id,
                    width=512,
                    height=512,
                    num_inference_steps=60,
                    guidance_scale=7.5
                )
                
                if result:
                    success_count += 1
                    logger.info(f"✅ {config['description']} gerado!")
                else:
                    logger.error(f"❌ Falha: {config['description']}")
                    
            except Exception as e:
                logger.error(f"❌ Erro em {config['description']}: {e}")
        
        logger.info(f"🎯 UI Assets: {success_count}/{len(ui_assets)} gerados")
        return success_count > 0
    
    def cleanup(self):
        """Limpa recursos GPU."""
        if self.pipeline:
            self.pipeline.cleanup()
    
    def run_complete_generation(self):
        """Executa geração completa de todos os assets."""
        logger.info("🎮 === MEDIEVAL DECK - GERAÇÃO COMPLETA DE ASSETS ===\n")
        
        if not self.initialize():
            return False
        
        try:
            # Gerar todos os tipos de assets
            bg_success = self.generate_backgrounds()
            anim_success = self.generate_character_animations()
            ui_success = self.generate_ui_assets()
            
            # Resumo final
            logger.info("\n🏆 === RESUMO FINAL ===")
            logger.info(f"✅ Backgrounds: {'OK' if bg_success else 'FALHOU'}")
            logger.info(f"✅ Animações: {'OK' if anim_success else 'FALHOU'}")
            logger.info(f"✅ UI Assets: {'OK' if ui_success else 'FALHOU'}")
            
            total_success = sum([bg_success, anim_success, ui_success])
            
            if total_success >= 2:
                logger.info(f"\n🎉 GERAÇÃO CONCLUÍDA COM SUCESSO!")
                logger.info(f"📁 Assets salvos em: assets/generated/ e assets/sprite_sheets/")
                logger.info(f"🎮 Execute o jogo para ver os novos assets!")
                return True
            else:
                logger.error(f"\n❌ Muitas falhas na geração ({total_success}/3 sucessos)")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro durante geração completa: {e}")
            return False
        
        finally:
            self.cleanup()


def main():
    """Função principal."""
    generator = MedievalAssetGenerator()
    success = generator.run_complete_generation()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
