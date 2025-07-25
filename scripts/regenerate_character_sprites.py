#!/usr/bin/env python3
"""
Regenera sprites de personagens com background totalmente transparente.
Remove fundos residuais e melhora qualidade dos sprites.
"""
import sys
import os
from pathlib import Path

# Adicionar src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def regenerate_character_sprites():
    """Regenera sprites de personagens com transparência perfeita."""
    try:
        print("=== Regenerando Sprites de Personagens ===")
        
        import torch
        from diffusers import DiffusionPipeline
        from PIL import Image, ImageOps
        import numpy as np
        import json
        
        # Carregar pipeline SDXL
        print("🔄 Carregando pipeline SDXL...")
        pipe = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            use_safetensors=True,
            variant="fp16" if torch.cuda.is_available() else None,
            cache_dir="assets/cache"
        )
        
        if torch.cuda.is_available():
            pipe = pipe.to("cuda")
            pipe.enable_model_cpu_offload()
            pipe.enable_vae_slicing()
            
        print("✅ Pipeline carregado!")
        
        # Sprites de personagens para regenerar
        characters = {
            "knight_sprite": {
                "prompt": "medieval knight character, full body portrait, armored warrior, sword and shield, heroic pose, detailed armor, fantasy art style, clean background, high quality, masterpiece",
                "negative": "background, scenery, multiple characters, text, low quality, blurry, artifacts, complex background",
                "class": "warrior"
            },
            "wizard_sprite": {
                "prompt": "medieval wizard character, full body portrait, robed mage with staff, magical aura, mystical appearance, detailed robes, fantasy art style, clean background, high quality, masterpiece", 
                "negative": "background, scenery, multiple characters, text, low quality, blurry, artifacts, complex background",
                "class": "mage"
            },
            "rogue_sprite": {
                "prompt": "medieval rogue character, full body portrait, hooded assassin with daggers, stealthy pose, leather armor, fantasy art style, clean background, high quality, masterpiece",
                "negative": "background, scenery, multiple characters, text, low quality, blurry, artifacts, complex background", 
                "class": "rogue"
            },
            "archer_sprite": {
                "prompt": "medieval archer character, full body portrait, ranger with bow, forest guardian, detailed leather armor, fantasy art style, clean background, high quality, masterpiece",
                "negative": "background, scenery, multiple characters, text, low quality, blurry, artifacts, complex background",
                "class": "ranger"
            },
            "paladin_sprite": {
                "prompt": "medieval paladin character, full body portrait, holy warrior with blessed armor, divine aura, ceremonial weapons, fantasy art style, clean background, high quality, masterpiece",
                "negative": "background, scenery, multiple characters, text, low quality, blurry, artifacts, complex background",
                "class": "paladin"
            }
        }
        
        def remove_background(image):
            """Remove background usando threshold de cor."""
            # Converter para RGBA se necessário
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Converter para array numpy
            data = np.array(image)
            
            # Detectar pixels de background (geralmente claros ou uniformes nas bordas)
            # Usar as bordas como referência para cor de background
            border_colors = []
            h, w = data.shape[:2]
            
            # Coletar cores das bordas
            border_colors.extend(data[0, :].tolist())  # Top
            border_colors.extend(data[-1, :].tolist())  # Bottom  
            border_colors.extend(data[:, 0].tolist())  # Left
            border_colors.extend(data[:, -1].tolist())  # Right
            
            # Encontrar cor mais comum nas bordas
            from collections import Counter
            most_common_color = Counter(tuple(c[:3]) for c in border_colors).most_common(1)[0][0]
            
            # Criar máscara para remover background similar
            threshold = 40  # Tolerância para cores similares
            mask = np.all(np.abs(data[:,:,:3] - most_common_color) < threshold, axis=2)
            
            # Tornar pixels de background transparentes
            data[mask] = [0, 0, 0, 0]
            
            return Image.fromarray(data, 'RGBA')
        
        # Gerar cada sprite
        results = {}
        for sprite_name, config in characters.items():
            print(f"\n🎨 Gerando {sprite_name}...")
            
            # Configurações otimizadas para sprites
            image = pipe(
                prompt=config["prompt"],
                negative_prompt=config["negative"],
                height=1024,  # Alta resolução para sprites
                width=1024,
                num_inference_steps=80,
                guidance_scale=9.0,  # Maior controle
                num_images_per_prompt=1
            ).images[0]
            
            # Remover background automaticamente
            image_transparent = remove_background(image)
            
            # Pós-processamento adicional
            # Ajustar contraste para melhor definição
            image_transparent = ImageOps.autocontrast(image_transparent, cutoff=1)
            
            # Salvar sprite transparente
            output_path = Path("assets/generated") / f"{sprite_name}_transparent.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image_transparent.save(output_path, "PNG")
            
            # Também salvar versão original para comparação
            original_path = Path("assets/generated") / f"{sprite_name}_original.png"
            image.save(original_path, "PNG")
            
            print(f"✅ {sprite_name} salvo em: {output_path}")
            results[sprite_name] = {
                "transparent": str(output_path),
                "original": str(original_path),
                "class": config["class"]
            }
            
            # Limpar memória
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        # Salvar manifesto de sprites
        manifest_path = Path("assets/generated/sprites_manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump({
                "generated_at": "2025-01-25",
                "version": "2.0", 
                "sprites": results,
                "quality": "premium_transparent"
            }, f, indent=2)
            
        print(f"\n🎉 Todos os sprites regenerados com transparência!")
        print(f"📋 Manifesto salvo em: {manifest_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = regenerate_character_sprites()
    if success:
        print("\n✅ Sprites de personagens regenerados com transparência!")
    else:
        print("\n❌ Falha na regeneração dos sprites")
