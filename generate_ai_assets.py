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
    
    print("\n🎉 Geração concluída! Assets prontos para nova tela de seleção.")
    
except Exception as e:
    print(f"❌ Erro geral: {e}")
    import traceback
    traceback.print_exc()