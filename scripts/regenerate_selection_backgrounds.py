#!/usr/bin/env python3
"""
Regenera backgrounds da tela de seleção com qualidade premium.
Remove bugs visuais e melhora consistência.
"""
import sys
import os
from pathlib import Path

# Adicionar src ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def regenerate_selection_backgrounds():
    """Regenera backgrounds da tela de seleção com prompts otimizados."""
    try:
        print("=== Regenerando Backgrounds da Tela de Seleção ===")
        
        import torch
        from diffusers import DiffusionPipeline
        from PIL import Image, ImageOps
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
            # Otimizar memória
            pipe.enable_model_cpu_offload()
            pipe.enable_vae_slicing()
            
        print("✅ Pipeline carregado!")
        
        # Prompts otimizados para backgrounds de seleção
        backgrounds = {
            "character_selection_bg": {
                "prompt": "medieval fantasy character selection hall, ornate stone architecture, mystical glowing portals, ancient library atmosphere, golden light streaming through tall windows, magical runes on walls, ethereal mist, cinematic lighting, high detail, masterpiece",
                "negative": "characters, people, faces, weapons, clutter, modern elements, low quality, blurry, artifacts",
                "size": (1920, 1080)
            },
            "deck_selection_bg": {
                "prompt": "medieval fantasy card table room, wooden round table with mystical glow, ancient tome shelves, candlelight ambiance, magical card deck floating above table, warm golden lighting, gothic architecture, high quality, detailed",
                "negative": "cards visible, text, people, characters, modern items, low quality, blurry",
                "size": (1920, 1080)
            },
            "main_menu_bg": {
                "prompt": "epic medieval fantasy castle main hall, massive stone pillars, royal banners hanging, throne room atmosphere, dramatic lighting through stained glass, mystical energy particles, cinematic composition, masterpiece quality",
                "negative": "people, characters, text, UI elements, modern objects, low quality, artifacts",
                "size": (1920, 1080)
            },
            "settings_bg": {
                "prompt": "medieval fantasy wizard study room, ancient scrolls and books, magical instruments on shelves, soft candlelight, mystical atmosphere, detailed stone walls, enchanted artifacts, warm ambient lighting",
                "negative": "people, readable text, modern elements, clutter, low quality, blurry",
                "size": (1920, 1080)
            }
        }
        
        # Gerar cada background
        results = {}
        for bg_name, config in backgrounds.items():
            print(f"\n🎨 Gerando {bg_name}...")
            
            # Configurações de qualidade premium
            image = pipe(
                prompt=config["prompt"],
                negative_prompt=config["negative"],
                height=config["size"][1],
                width=config["size"][0],
                num_inference_steps=80,  # Alta qualidade
                guidance_scale=8.5,
                num_images_per_prompt=1
            ).images[0]
            
            # Pós-processamento para melhorar qualidade
            # Ajustar contraste e saturação
            image = ImageOps.autocontrast(image, cutoff=1)
            
            # Salvar em alta qualidade
            output_path = Path("assets/generated") / f"{bg_name}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, "PNG", quality=95, optimize=True)
            
            print(f"✅ {bg_name} salvo em: {output_path}")
            results[bg_name] = str(output_path)
            
            # Limpar memória GPU após cada geração
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        # Salvar manifesto de backgrounds
        manifest_path = Path("assets/generated/backgrounds_manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump({
                "generated_at": "2025-01-25",
                "version": "2.0",
                "backgrounds": results,
                "quality": "premium"
            }, f, indent=2)
            
        print(f"\n🎉 Todos os backgrounds regenerados com sucesso!")
        print(f"📋 Manifesto salvo em: {manifest_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = regenerate_selection_backgrounds()
    if success:
        print("\n✅ Backgrounds da tela de seleção regenerados!")
    else:
        print("\n❌ Falha na regeneração dos backgrounds")
