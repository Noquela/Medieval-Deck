#!/usr/bin/env python3
"""
Sistema completo de regeneração de assets para Medieval Deck.

Gera todos os assets necessários:
- Backgrounds únicos para cada personagem
- Backgrounds únicos para cada tipo de inimigo  
- Sprites melhorados e transparentes
- Assets de UI temáticos
- Animações e efeitos visuais
"""

import sys
import logging
from pathlib import Path
import numpy as np
from PIL import Image

# Add src to path for imports
src_path = Path(__file__).parent / "src"
project_root = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.utils.helpers import setup_logging
from src.models.sdxl_pipeline import SDXLPipeline
from src.generators.asset_generator import AssetGenerator


def setup_enhanced_asset_generator():
    """
    Configura o gerador de assets com prompts melhorados.
    """
    
    # Character-specific backgrounds (mais detalhados)
    CHARACTER_BACKGROUNDS = {
        "knight": {
            "prompt": "epic medieval castle throne room at golden hour, massive stone columns with heraldic banners, ornate golden throne, sunlight streaming through stained glass windows, armor stands with gleaming weapons, red carpet leading to throne, regal atmosphere, no people, architectural masterpiece",
            "negative": "people, humans, characters, figures, persons, crowds, soldiers, guards",
            "width": 3440,
            "height": 1440,
            "filename": "knight_bg.png"
        },
        "wizard": {
            "prompt": "mystical arcane sanctum, floating crystal orbs emitting blue light, ancient spell circles carved in stone floor, levitating books with glowing runes, mystical purple mist, magical artifacts on pedestals, starry void visible through arched windows, ethereal atmosphere, no people, magical masterpiece",
            "negative": "people, humans, characters, figures, persons, wizards, mages, sorcerers",
            "width": 3440,
            "height": 1440,
            "filename": "wizard_bg.png"
        },
        "assassin": {
            "prompt": "dark gothic underground lair, stone tunnels with flickering torches, hidden weapon cache on walls, mysterious green alchemical vials glowing, shadowy alcoves, underground river with stone bridges, moonlight through grates, sinister atmosphere, no people, noir masterpiece",
            "negative": "people, humans, characters, figures, persons, assassins, rogues, thieves",
            "width": 3440,
            "height": 1440,
            "filename": "assassin_bg.png"
        }
    }
    
    # Enemy-specific combat backgrounds
    ENEMY_BACKGROUNDS = {
        "goblin": {
            "prompt": "chaotic goblin cave with crude wooden spikes, scattered bones and rusty weapons, primitive totems, flickering campfire with cooking pot, stolen treasure scattered around, damp cave walls with moss, eerie green light, dangerous atmosphere, no creatures",
            "negative": "goblins, creatures, monsters, people, humans, characters",
            "width": 3440,
            "height": 1440,
            "filename": "combat_bg_goblin_cave.png"
        },
        "orc": {
            "prompt": "brutal orc war camp, massive bone structures, war drums and weapon racks, tribal banners made of hide, blazing fire pits, skull decorations, muddy ground with weapon marks, intimidating atmosphere, no creatures",
            "negative": "orcs, creatures, monsters, people, humans, characters",
            "width": 3440,
            "height": 1440,
            "filename": "combat_bg_orc_camp.png"
        },
        "skeleton": {
            "prompt": "haunted bone catacombs, ancient coffins and sarcophagi, ghostly blue flames floating in air, cracked stone walls with carved skulls, eerie mist, bone piles, undead necromantic atmosphere, spectral lighting, no undead creatures",
            "negative": "skeletons, zombies, undead, creatures, monsters, people, humans",
            "width": 3440,
            "height": 1440,
            "filename": "combat_bg_skeleton_crypt.png"
        },
        "dragon": {
            "prompt": "epic dragon's volcanic lair, massive obsidian cavern with lava pools, treasure hoard of gold and gems, ancient pillars carved with draconic runes, molten lava waterfalls, crystal formations, epic scale architecture, no dragons",
            "negative": "dragons, creatures, monsters, people, humans, characters",
            "width": 3440,
            "height": 1440,
            "filename": "combat_bg_dragon_lair.png"
        },
        "dark_mage": {
            "prompt": "corrupted wizard tower, dark magical laboratory with bubbling cauldrons, floating dark crystals, forbidden spell books, ominous purple energy, twisted magical apparatus, sinister alchemical setup, dark magic atmosphere, no mages",
            "negative": "wizards, mages, people, humans, characters, figures, persons",
            "width": 3440,
            "height": 1440,
            "filename": "combat_bg_dark_tower.png"
        }
    }
    
    # Enhanced character sprites
    CHARACTER_SPRITES = {
        "knight": {
            "prompt": "heroic medieval knight in ornate golden plate armor, noble stance with sword and shield, detailed engravings on armor, flowing red cape, majestic helmet with plume, full body portrait, epic heroic proportions, masterpiece character art",
            "negative": "background, scenery, landscape, environment, multiple people",
            "width": 512,
            "height": 768,
            "filename": "knight_sprite_enhanced.png"
        },
        "wizard": {
            "prompt": "wise arcane wizard in flowing blue robes with mystical symbols, staff with glowing crystal orb, long white beard, pointed hat with stars, magical aura surrounding figure, full body portrait, detailed character art",
            "negative": "background, scenery, landscape, environment, multiple people",
            "width": 512,
            "height": 768,
            "filename": "wizard_sprite_enhanced.png"
        },
        "assassin": {
            "prompt": "stealthy assassin in dark hood and leather armor, twin daggers, mysterious cloak, green poison vials on belt, shadowy appearance, agile stance, full body portrait, detailed rogue character art",
            "negative": "background, scenery, landscape, environment, multiple people",
            "width": 512,
            "height": 768,
            "filename": "assassin_sprite_enhanced.png"
        }
    }
    
    # Enhanced enemy sprites
    ENEMY_SPRITES = {
        "goblin": {
            "prompt": "menacing goblin warrior with crude armor and jagged sword, green skin, pointed ears, savage expression, tribal markings, full body portrait, detailed monster art",
            "negative": "background, scenery, landscape, environment, multiple creatures",
            "width": 512,
            "height": 768,
            "filename": "goblin_sprite_enhanced.png"
        },
        "orc": {
            "prompt": "massive orc berserker with spiked armor and war axe, muscular build, tusks, brutal appearance, war paint, full body portrait, intimidating monster art",
            "negative": "background, scenery, landscape, environment, multiple creatures",
            "width": 512,
            "height": 768,
            "filename": "orc_sprite_enhanced.png"
        },
        "skeleton": {
            "prompt": "undead skeleton warrior in tattered armor with bone sword, glowing blue eyes, ethereal aura, ancient warrior appearance, full body portrait, undead creature art",
            "negative": "background, scenery, landscape, environment, multiple creatures",
            "width": 512,
            "height": 768,
            "filename": "skeleton_sprite_enhanced.png"
        },
        "dragon": {
            "prompt": "majestic ancient red dragon with massive wings spread, fierce expression, scales gleaming, powerful claws, epic proportions, full body portrait, legendary creature art",
            "negative": "background, scenery, landscape, environment, multiple creatures",
            "width": 768,
            "height": 768,
            "filename": "dragon_sprite_enhanced.png"
        },
        "dark_mage": {
            "prompt": "sinister dark wizard in black robes with glowing staff, hood casting shadow over face, dark magical aura, corrupted appearance, full body portrait, evil mage art",
            "negative": "background, scenery, landscape, environment, multiple people",
            "width": 512,
            "height": 768,
            "filename": "dark_mage_sprite_enhanced.png"
        }
    }
    
    return CHARACTER_BACKGROUNDS, ENEMY_BACKGROUNDS, CHARACTER_SPRITES, ENEMY_SPRITES


def check_if_asset_exists_and_valid(asset_generator, filename, min_size_kb=100, min_resolution=(100, 100)):
    """
    Verifica se um asset existe e se tem qualidade adequada.
    
    Args:
        asset_generator: Gerador de assets
        filename: Nome do arquivo a verificar
        min_size_kb: Tamanho mínimo do arquivo em KB (default: 100KB)
        min_resolution: Tupla (width, height) com resolução mínima (default: 100x100)
        
    Returns:
        tuple: (bool, str) - (é válido, motivo se inválido)
    """
    asset_path = asset_generator.generated_dir / filename
    
    if not asset_path.exists():
        return False, "Arquivo não existe"
    
    try:
        # Verificar se o arquivo não está corrompido e tem tamanho adequado
        file_size = asset_path.stat().st_size
        
        # Arquivo muito pequeno provavelmente está corrompido
        if file_size < min_size_kb * 1024:
            return False, f"Arquivo muito pequeno ({file_size/1024:.1f}KB < {min_size_kb}KB)"
            
        # Tentar abrir a imagem para verificar se não está corrompida
        from PIL import Image
        with Image.open(asset_path) as img:
            width, height = img.size
            
            # Verificar se tem resolução mínima
            if width < min_resolution[0] or height < min_resolution[1]:
                return False, f"Resolução muito baixa ({width}x{height} < {min_resolution[0]}x{min_resolution[1]})"
                
            # Verificar se a imagem não está totalmente preta ou branca (possível corrupção)
            import numpy as np
            img_array = np.array(img.convert('RGB'))
            
            # Se toda a imagem for da mesma cor, provavelmente está corrompida
            unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[-1]), axis=0))
            if unique_colors < 10:  # Menos de 10 cores únicas é suspeito
                return False, f"Imagem com poucas cores únicas ({unique_colors}), possível corrupção"
                
        return True, "Válido"
        
    except Exception:
        # Se houver erro ao abrir, o arquivo está corrompido
        return False


def generate_character_backgrounds(asset_generator, character_backgrounds):
    """Gera backgrounds únicos para cada personagem (apenas os que estão faltando)."""
    logger = logging.getLogger(__name__)
    logger.info("🎭 Verificando e gerando backgrounds únicos para personagens...")
    
    generated = {}
    
    for char_id, bg_config in character_backgrounds.items():
        filename = bg_config["filename"]
        
        # Verificar se já existe e é válido (background precisa ser maior - 1MB+ e resolução HD)
        is_valid, reason = check_if_asset_exists_and_valid(
            asset_generator, 
            filename, 
            min_size_kb=1000,  # 1MB mínimo para backgrounds
            min_resolution=(1000, 1000)  # Resolução mínima para backgrounds
        )
        
        if is_valid:
            logger.info(f"  ✅ Background já existe e é válido: {char_id} -> {filename}")
            generated[char_id] = str(asset_generator.generated_dir / filename)
            continue
        else:
            logger.info(f"  ⚠️ Background precisa ser regenerado: {char_id} -> {reason}")
            
        # Só gerar se não existir ou estiver corrompido
        try:
            logger.info(f"  📸 Gerando background faltante para {char_id}...")
            
            # Gerar background usando o método correto
            image = asset_generator._generate_image_from_prompt(
                prompt=bg_config["prompt"],
                width=bg_config["width"],
                height=bg_config["height"]
            )
            
            if image:
                # Salvar imagem
                output_path = asset_generator.generated_dir / filename
                image.save(output_path, "PNG", quality=95)
                
                generated[char_id] = str(output_path)
                logger.info(f"  ✅ Background gerado: {char_id} -> {output_path}")
            else:
                logger.error(f"  ❌ Falha ao gerar background: {char_id}")
                
        except Exception as e:
            logger.error(f"  💥 Erro ao gerar background {char_id}: {e}")
    
    return generated


def generate_enemy_backgrounds(asset_generator, enemy_backgrounds):
    """Gera backgrounds únicos para cada tipo de inimigo (apenas os que estão faltando)."""
    logger = logging.getLogger(__name__)
    logger.info("👹 Verificando e gerando backgrounds únicos para inimigos...")
    
    generated = {}
    
    for enemy_id, bg_config in enemy_backgrounds.items():
        filename = bg_config["filename"]
        
        # Verificar se já existe e é válido (background precisa ser maior - 1MB+ e resolução HD)
        is_valid, reason = check_if_asset_exists_and_valid(
            asset_generator, 
            filename, 
            min_size_kb=1000,  # 1MB mínimo para backgrounds
            min_resolution=(1000, 1000)  # Resolução mínima para backgrounds
        )
        
        if is_valid:
            logger.info(f"  ✅ Background já existe e é válido: {enemy_id} -> {filename}")
            generated[enemy_id] = str(asset_generator.generated_dir / filename)
            continue
        else:
            logger.info(f"  ⚠️ Background precisa ser regenerado: {enemy_id} -> {reason}")
            
        # Só gerar se não existir ou estiver corrompido
        try:
            logger.info(f"  📸 Gerando background faltante para {enemy_id}...")
            
            # Gerar background usando o método correto
            image = asset_generator._generate_image_from_prompt(
                prompt=bg_config["prompt"],
                width=bg_config["width"],
                height=bg_config["height"]
            )
            
            if image:
                # Salvar imagem
                output_path = asset_generator.generated_dir / filename
                image.save(output_path, "PNG", quality=95)
                
                generated[enemy_id] = str(output_path)
                logger.info(f"  ✅ Background gerado: {enemy_id} -> {output_path}")
            else:
                logger.error(f"  ❌ Falha ao gerar background: {enemy_id}")
                
        except Exception as e:
            logger.error(f"  💥 Erro ao gerar background {enemy_id}: {e}")
    
    return generated


def generate_enhanced_sprites(asset_generator, sprite_configs):
    """Gera sprites melhorados (apenas os que estão faltando)."""
    logger = logging.getLogger(__name__)
    logger.info("🎨 Verificando e gerando sprites melhorados...")
    
    # Usar a nova função do AssetGenerator que acabamos de implementar
    try:
        generated_paths = asset_generator.generate_enhanced_sprites(
            sprite_configs=sprite_configs,
            force_regenerate=False  # Só gerar se não existir ou estiver corrompido
        )
        
        # A validação já é feita internamente pelo AssetGenerator
        return generated_paths
        
    except Exception as e:
        logger.error(f"💥 Erro ao gerar sprites melhorados: {e}")
        return {}


def force_regenerate_knight_bg_if_problematic(asset_generator, character_backgrounds):
    """
    Verifica especificamente o knight_bg.png e força regeneração se estiver com problema.
    """
    logger = logging.getLogger(__name__)
    
    knight_bg_path = asset_generator.generated_dir / "knight_bg.png"
    
    # Verificações específicas para o background do knight
    needs_regeneration = False
    reason = ""
    
    if not knight_bg_path.exists():
        needs_regeneration = True
        reason = "Arquivo não existe"
    else:
        try:
            # Verificar tamanho do arquivo
            file_size = knight_bg_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size < 1024 * 1024:  # Menor que 1MB é suspeito
                needs_regeneration = True
                reason = f"Arquivo muito pequeno ({file_size_mb:.1f}MB)"
            
            # Verificar se consegue abrir a imagem
            from PIL import Image
            with Image.open(knight_bg_path) as img:
                width, height = img.size
                if width < 1000 or height < 1000:  # Resolução muito baixa
                    needs_regeneration = True
                    reason = f"Resolução muito baixa ({width}x{height})"
                    
        except Exception as e:
            needs_regeneration = True
            reason = f"Erro ao ler arquivo: {e}"
    
    if needs_regeneration:
        logger.warning(f"🔧 knight_bg.png precisa ser regenerado: {reason}")
        
        # Forçar regeneração do knight background
        if "knight" in character_backgrounds:
            try:
                bg_config = character_backgrounds["knight"]
                logger.info("🏰 Regenerando knight_bg.png...")
                
                image = asset_generator._generate_image_from_prompt(
                    prompt=bg_config["prompt"],
                    width=bg_config["width"], 
                    height=bg_config["height"]
                )
                
                if image:
                    output_path = asset_generator.generated_dir / bg_config["filename"]
                    image.save(output_path, "PNG", quality=95)
                    logger.info(f"✅ knight_bg.png regenerado com sucesso: {output_path}")
                    return True
                else:
                    logger.error("❌ Falha ao regenerar knight_bg.png")
                    return False
                    
            except Exception as e:
                logger.error(f"💥 Erro ao regenerar knight_bg.png: {e}")
                return False
    else:
        logger.info("✅ knight_bg.png está em boas condições")
        return True


def main():
    """Função principal do regenerador completo."""
    # Setup logging
    logger = setup_logging(level="INFO")
    logger.info("🎮 Medieval Deck - Sistema Completo de Regeneração")
    
    try:
        # Initialize configuration
        config = Config()
        
        # Initialize AI pipeline
        logger.info("🤖 Inicializando pipeline SDXL...")
        pipeline = SDXLPipeline(
            model_id=config.ai.model_id,
            refiner_id=config.ai.refiner_id,
            enable_refiner=config.ai.enable_refiner,
            device=config.get_device(),
            cache_dir=str(config.assets_cache_dir),
            memory_efficient=config.ai.memory_efficient
        )
        
        # Initialize asset generator
        logger.info("🎨 Inicializando gerador de assets...")
        asset_generator = AssetGenerator(
            config=config,
            sdxl_pipeline=pipeline,
            cache_dir=str(config.assets_cache_dir)
        )
        
        # Setup enhanced configurations
        char_bgs, enemy_bgs, char_sprites, enemy_sprites = setup_enhanced_asset_generator()
        
        # Verificação especial para knight_bg.png
        logger.info("🔍 Verificando especificamente o knight_bg.png...")
        force_regenerate_knight_bg_if_problematic(asset_generator, char_bgs)
        
        # Generate all assets (apenas os que estão faltando)
        logger.info("🚀 Iniciando verificação e geração inteligente de assets...")
        
        # 1. Character backgrounds (apenas os faltantes)
        char_bg_results = generate_character_backgrounds(asset_generator, char_bgs)
        
        # 2. Enemy backgrounds (apenas os faltantes)
        enemy_bg_results = generate_enemy_backgrounds(asset_generator, enemy_bgs)
        
        # 3. Enhanced character sprites (apenas os faltantes)
        char_sprite_results = generate_enhanced_sprites(asset_generator, char_sprites)
        
        # 4. Enhanced enemy sprites (apenas os faltantes)
        enemy_sprite_results = generate_enhanced_sprites(asset_generator, enemy_sprites)
        
        # Report results
        total_generated = (
            len(char_bg_results) + 
            len(enemy_bg_results) + 
            len(char_sprite_results) + 
            len(enemy_sprite_results)
        )
        
        logger.info("🎉 Geração completa finalizada!")
        logger.info(f"📊 Total de assets gerados: {total_generated}")
        logger.info(f"  🎭 Backgrounds de personagens: {len(char_bg_results)}")
        logger.info(f"  👹 Backgrounds de inimigos: {len(enemy_bg_results)}")
        logger.info(f"  🎨 Sprites de personagens: {len(char_sprite_results)}")
        logger.info(f"  👾 Sprites de inimigos: {len(enemy_sprite_results)}")
        
        return True
        
    except Exception as e:
        logger.error(f"💥 Erro fatal durante a geração: {e}", exc_info=True)
        return False
    
    finally:
        # Cleanup
        if 'pipeline' in locals():
            logger.info("🧹 Limpando pipeline...")
            pipeline.unload_models()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
