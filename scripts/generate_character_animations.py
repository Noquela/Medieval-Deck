#!/usr/bin/env python3
"""
Gera sprite sheets de animação 30fps para todos os personagens.
Cria animações de idle, attack, cast, hurt com frames suaves.
"""
import sys
import os
from pathlib import Path

# Adicionar src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def generate_character_animations():
    """Gera animações 30fps para todos os personagens."""
    try:
        print("=== Gerando Animações de Personagens 30fps ===")
        
        import torch
        from diffusers import DiffusionPipeline
        from PIL import Image, ImageOps, ImageDraw
        import numpy as np
        import json
        import math
        
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
        
        # Definições de personagens e animações
        characters = {
            "knight": {
                "base_prompt": "medieval knight character, detailed armor, heroic warrior",
                "class": "warrior"
            },
            "wizard": {
                "base_prompt": "medieval wizard character, mystical robes, magical staff",
                "class": "mage"
            },
            "rogue": {
                "base_prompt": "medieval rogue character, leather armor, hooded assassin",
                "class": "rogue"
            },
            "archer": {
                "base_prompt": "medieval archer character, forest ranger, bow weapon",
                "class": "ranger"
            },
            "goblin": {
                "base_prompt": "goblin warrior enemy, green skin, crude weapons",
                "class": "enemy"
            },
            "orc": {
                "base_prompt": "orc berserker enemy, muscular, brutal weapons",
                "class": "enemy"
            },
            "skeleton": {
                "base_prompt": "skeleton warrior enemy, undead, bone armor",
                "class": "enemy"
            },
            "dragon": {
                "base_prompt": "dragon creature, massive wings, powerful beast",
                "class": "boss"
            }
        }
        
        # Tipos de animação com configurações específicas
        animations = {
            "idle": {
                "frames": 8,
                "descriptions": [
                    "standing pose, relaxed stance",
                    "slight lean forward, alert",
                    "breathing motion, calm",
                    "weight shift left foot",
                    "neutral pose, centered",
                    "weight shift right foot", 
                    "slight lean back, confident",
                    "return to standing pose"
                ]
            },
            "attack": {
                "frames": 6,
                "descriptions": [
                    "preparing to strike, weapon raised",
                    "mid-swing, weapon moving",
                    "strike impact, weapon extended",
                    "follow through, weight forward",
                    "recovery pose, weapon lowering",
                    "return to ready stance"
                ]
            },
            "cast": {
                "frames": 8,
                "descriptions": [
                    "gathering magical energy, hands glowing",
                    "channeling spell, energy building",
                    "spell formation, magic circles",
                    "power peak, bright magical aura",
                    "spell release, energy projection",
                    "magic dissipating, hands lowering",
                    "spell completion, calm stance",
                    "return to neutral pose"
                ]
            },
            "hurt": {
                "frames": 4,
                "descriptions": [
                    "impact reaction, staggering back",
                    "pain expression, doubled over",
                    "recovery attempt, struggling up",
                    "defensive stance, ready again"
                ]
            }
        }
        
        def create_sprite_sheet(frames, output_path):
            """Cria sprite sheet horizontal com todos os frames."""
            if not frames:
                return None
                
            frame_width = frames[0].width
            frame_height = frames[0].height
            sheet_width = frame_width * len(frames)
            
            # Criar sprite sheet
            sprite_sheet = Image.new('RGBA', (sheet_width, frame_height), (0, 0, 0, 0))
            
            for i, frame in enumerate(frames):
                x_pos = i * frame_width
                sprite_sheet.paste(frame, (x_pos, 0))
            
            # Salvar sprite sheet
            sprite_sheet.save(output_path, "PNG")
            return sprite_sheet
        
        def remove_background(image):
            """Remove background mantendo apenas o personagem."""
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            data = np.array(image)
            
            # Detectar background usando bordas
            h, w = data.shape[:2]
            border_samples = []
            border_samples.extend(data[0, :, :3].tolist())
            border_samples.extend(data[-1, :, :3].tolist())
            border_samples.extend(data[:, 0, :3].tolist())
            border_samples.extend(data[:, -1, :3].tolist())
            
            # Cor de background mais comum
            from collections import Counter
            bg_color = Counter(tuple(c) for c in border_samples).most_common(1)[0][0]
            
            # Criar máscara
            threshold = 50
            mask = np.all(np.abs(data[:,:,:3] - bg_color) < threshold, axis=2)
            data[mask] = [0, 0, 0, 0]
            
            return Image.fromarray(data, 'RGBA')
        
        # Gerar animações para cada personagem
        results = {}
        total_animations = len(characters) * len(animations)
        current = 0
        
        for char_name, char_config in characters.items():
            print(f"\n👤 Gerando animações para {char_name}...")
            char_results = {}
            
            for anim_name, anim_config in animations.items():
                current += 1
                print(f"  🎬 {anim_name} ({current}/{total_animations})")
                
                frames = []
                base_seed = hash(f"{char_name}_{anim_name}") % (2**32)
                
                # Gerar cada frame da animação
                for frame_idx in range(anim_config["frames"]):
                    frame_desc = anim_config["descriptions"][frame_idx % len(anim_config["descriptions"])]
                    
                    # Prompt completo para o frame
                    full_prompt = f"{char_config['base_prompt']}, {frame_desc}, fantasy art style, detailed character design, clean background, high quality, masterpiece"
                    
                    negative_prompt = "multiple characters, background scenery, text, low quality, blurry, artifacts, complex background, weapons floating"
                    
                    # Gerar frame
                    generator = torch.Generator().manual_seed(base_seed + frame_idx)
                    
                    frame_image = pipe(
                        prompt=full_prompt,
                        negative_prompt=negative_prompt,
                        height=512,
                        width=512,
                        num_inference_steps=60,
                        guidance_scale=8.5,
                        generator=generator,
                        num_images_per_prompt=1
                    ).images[0]
                    
                    # Remover background e processar
                    frame_transparent = remove_background(frame_image)
                    frame_processed = ImageOps.autocontrast(frame_transparent, cutoff=1)
                    
                    frames.append(frame_processed)
                    
                    print(f"    Frame {frame_idx + 1}/{anim_config['frames']} ✅")
                
                # Criar sprite sheet para a animação
                sprite_sheet_path = Path("assets/generated/animations") / f"{char_name}_{anim_name}_sheet.png"
                sprite_sheet_path.parent.mkdir(parents=True, exist_ok=True)
                
                sprite_sheet = create_sprite_sheet(frames, sprite_sheet_path)
                
                char_results[anim_name] = {
                    "sprite_sheet": str(sprite_sheet_path),
                    "frames": len(frames),
                    "fps": 30,
                    "loop": anim_name in ["idle"],  # Apenas idle faz loop
                    "size": [frames[0].width, frames[0].height] if frames else [512, 512]
                }
                
                print(f"  ✅ {anim_name}: {len(frames)} frames -> {sprite_sheet_path}")
                
                # Limpar memória
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            results[char_name] = char_results
        
        # Salvar manifesto de animações
        manifest_path = Path("assets/generated/animations/animations_manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump({
                "generated_at": "2025-01-25",
                "version": "2.0",
                "fps": 30,
                "total_characters": len(characters),
                "total_animations": total_animations,
                "characters": results
            }, f, indent=2)
            
        print(f"\n🎉 Todas as animações 30fps geradas!")
        print(f"📋 Manifesto salvo em: {manifest_path}")
        print(f"📊 Total: {len(characters)} personagens, {total_animations} animações")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = generate_character_animations()
    if success:
        print("\n✅ Animações 30fps geradas com sucesso!")
    else:
        print("\n❌ Falha na geração das animações")
