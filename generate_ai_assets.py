"""
Script para gerar assets de IA - Medieval Deck
Foco na nova tela de seleção de personagens ultrawide
"""

import sys
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

print("🔥 Medieval Deck - AI Asset Generator")
print("Gerando assets para nova tela de seleção ultrawide...")

try:
    from src.utils.config import Config
    from src.models.sdxl_pipeline import SDXLPipeline
    from src.generators.asset_generator import AssetGenerator
    
    print("✅ Módulos carregados")
    
    config = Config()
    
    print("🚀 Inicializando SDXL...")
    pipeline = SDXLPipeline(
        model_id=config.ai.model_id,
        device=config.get_device(),
        cache_dir=str(config.assets_cache_dir),
        memory_efficient=True
    )
    
    print("🎨 Inicializando gerador...")
    asset_gen = AssetGenerator(config=config, sdxl_pipeline=pipeline)
    
    # Gerar fundos específicos para cada personagem (ultrawide 3440x1440)
    characters = [
        {
            "id": "knight_bg",
            "name": "Cavaleiro - Fundo",
            "prompt": "epic medieval knight in golden armor, cathedral courtyard at sunset, dramatic cinematic lighting, castle banners flying, masterpiece, high quality, detailed"
        },
        {
            "id": "wizard_bg", 
            "name": "Mago - Fundo",
            "prompt": "arcane mage in dark blue robes, ancient library with glowing runes, floating magic particles, mystical atmosphere, purple and blue lighting, masterpiece, high quality, detailed"
        },
        {
            "id": "assassin_bg",
            "name": "Assassino - Fundo", 
            "prompt": "dark rogue assassin in hood, purple misty fog, medieval stone alley at night, moonlight shadows, mysterious atmosphere, masterpiece, high quality, detailed"
        }
    ]
    
    print(f"� Gerando {len(characters)} fundos ultrawide...")
    
    generated_dir = Path(config.assets_generated_dir)
    
    for i, char in enumerate(characters, 1):
        print(f"[{i}/{len(characters)}] Gerando {char['name']}...")
        
        try:
            image = pipeline.generate_image(
                prompt=char["prompt"],
                width=3440,
                height=1440,
                guidance_scale=8.5,
                num_inference_steps=80
            )
            
            output_path = generated_dir / f"{char['id']}.png"
            image.save(output_path, "PNG", quality=95)
            
            print(f"  ✅ Salvo: {output_path.name}")
            
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    print("\n🎉 Geração de personagens concluída!")
    
    # ========================================
    # ETAPA B - ASSETS DE COMBATE
    # ========================================
    print("\n⚔️ Gerando assets de combate...")
    
    # 1. Background de combate épico
    print("🏰 Gerando background de combate...")
    combat_bg_path = asset_gen.generate_combat_bg()
    if combat_bg_path:
        print(f"  ✅ Combat background salvo: {Path(combat_bg_path).name}")
    
    # 2. Sprites de inimigos
    enemies_config = [
        {"id": "goblin_scout", "desc": "goblin warrior with rusty axe and leather armor"},
        {"id": "orc_berserker", "desc": "large orc with massive sword and spiked armor"},
        {"id": "skeleton_archer", "desc": "undead skeleton with longbow and tattered robes"},
        {"id": "dark_mage", "desc": "evil wizard in black robes with glowing staff"}
    ]
    
    print(f"👹 Gerando {len(enemies_config)} sprites de inimigos...")
    for enemy in enemies_config:
        enemy_path = asset_gen.generate_enemy_sprite(enemy["id"], enemy["desc"])
        if enemy_path:
            print(f"  ✅ {enemy['id']}: {Path(enemy_path).name}")
    
    # 3. Sprite do jogador
    print("🛡️ Gerando sprite do jogador...")
    player_path = asset_gen.generate_player_sprite("knight in golden armor with holy sword")
    if player_path:
        print(f"  ✅ Player sprite salvo: {Path(player_path).name}")
    
    print("\n🎉 Geração completa! Assets prontos para tela de combate.")
    
except Exception as e:
    print(f"❌ Erro geral: {e}")
    import traceback
    traceback.print_exc()