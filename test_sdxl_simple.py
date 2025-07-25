#!/usr/bin/env python3
"""
Teste mínimo de geração SDXL - gera apenas 1 sprite para verificar se funciona.
"""
import sys
import os
from pathlib import Path

def test_sdxl_generation():
    """Teste simples de geração SDXL"""
    try:
        print("=== Teste SDXL Mínimo ===")
        
        # Imports básicos
        import torch
        from diffusers import DiffusionPipeline
        from PIL import Image
        
        print(f"✅ PyTorch {torch.__version__}")
        print(f"✅ CUDA: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"✅ GPU: {torch.cuda.get_device_name()}")
            
        # Configurar pipeline SDXL
        print("🔄 Carregando pipeline SDXL...")
        
        pipe = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            use_safetensors=True,
            variant="fp16" if torch.cuda.is_available() else None
        )
        
        if torch.cuda.is_available():
            pipe = pipe.to("cuda")
            
        print("✅ Pipeline carregado!")
        
        # Prompt simples de teste
        prompt = "medieval knight character sprite, pixel art style, transparent background, high quality"
        
        print("🔄 Gerando imagem teste...")
        
        # Configurações conservadoras
        image = pipe(
            prompt,
            height=512,
            width=512,
            num_inference_steps=20,  # Poucos passos para teste rápido
            guidance_scale=7.5
        ).images[0]
        
        # Salvar resultado
        output_path = Path("test_sdxl_output.png")
        image.save(output_path)
        
        print(f"✅ Imagem gerada salva em: {output_path}")
        print("🎯 SDXL funcionando perfeitamente!")
        print("🎯 Pronto para gerar sprite sheets completos!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sdxl_generation()
    if success:
        print("\n🎉 Sistema pronto para gerar animações!")
    else:
        print("\n❌ Precisa resolver problemas antes de gerar animações")
