"""
Teste direto de geração 3440x1440 (Ultrawide QHD)
Testa a maior resolução ultrawide que a RTX 5070 consegue gerar.
"""

import sys
import logging
import torch
from pathlib import Path
import time

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.utils.config import Config
from src.utils.helpers import setup_logging
from src.models.sdxl_pipeline import SDXLPipeline

# Test ultrawide resolution
WIDTH = 3440
HEIGHT = 1440

TEST_PROMPT = """masterpiece, high quality, detailed, medieval fantasy castle on hilltop, 
dramatic sunset lighting, gothic architecture, stone walls, towers with flags, 
atmospheric clouds, cinematic composition, wide panoramic view"""

NEGATIVE_PROMPT = """blurry, low quality, pixelated, distorted, ugly, deformed, 
people, person, human, character, figure"""


def test_ultrawide():
    """Teste de geração ultrawide 3440x1440."""
    print("🏰 Medieval Deck - Teste Ultrawide 3440x1440")
    print("=" * 50)
    
    # Setup logging
    setup_logging(level="INFO")
    
    # Verificar GPU
    if torch.cuda.is_available():
        device = torch.cuda.current_device()
        gpu_name = torch.cuda.get_device_name(device)
        gpu_memory = torch.cuda.get_device_properties(device).total_memory / (1024**3)
        free_memory = torch.cuda.mem_get_info()[0] / (1024**3)
        
        print(f"🔥 GPU: {gpu_name}")
        print(f"💾 Memória Total: {gpu_memory:.1f} GB")
        print(f"🆓 Memória Livre: {free_memory:.1f} GB")
    else:
        print("❌ CUDA não disponível")
        return 1
    
    # Estimar VRAM necessário
    pixels = WIDTH * HEIGHT
    base_pixels = 1024 * 1024
    scale_factor = (pixels / base_pixels) ** 0.8
    estimated_vram = 6.5 + (scale_factor - 1) * 2.5
    
    print(f"\n📊 Resolução: {WIDTH}x{HEIGHT}")
    print(f"📊 Pixels: {pixels:,}")
    print(f"📊 VRAM estimado: {estimated_vram:.1f} GB")
    
    if estimated_vram > free_memory * 0.9:
        print(f"⚠️ Aviso: VRAM estimado ({estimated_vram:.1f} GB) próximo do limite ({free_memory:.1f} GB)")
    
    # Criar diretório de output
    output_dir = Path("test_ultrawide")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Inicializar configuração
        config = Config()
        
        # Inicializar pipeline
        print(f"\n🚀 Inicializando pipeline SDXL...")
        pipeline = SDXLPipeline(
            model_id=config.ai.model_id,
            refiner_id=config.ai.refiner_id,
            enable_refiner=False,  # Desabilitar para economizar VRAM
            device=config.get_device(),
            cache_dir=str(config.assets_cache_dir),
            memory_efficient=True
        )
        
        print("✅ Pipeline inicializado!")
        
        # Limpar cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
            # Memória antes
            memory_before = torch.cuda.memory_allocated() / (1024**3)
            print(f"\n📊 Memória GPU antes: {memory_before:.1f} GB")
        
        print(f"\n🎨 Gerando imagem {WIDTH}x{HEIGHT}...")
        print("⚡ Usando 25 steps para otimizar velocidade...")
        
        start_time = time.time()
        
        # Gerar imagem
        image = pipeline.generate_image(
            prompt=TEST_PROMPT,
            negative_prompt=NEGATIVE_PROMPT,
            width=WIDTH,
            height=HEIGHT,
            num_inference_steps=25,  # Reduzido para economizar VRAM
            guidance_scale=8.0  # Ligeiramente reduzido
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Salvar imagem
        output_path = output_dir / f"medieval_castle_ultrawide_{WIDTH}x{HEIGHT}.png"
        image.save(output_path)
        
        # Verificar memória após
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            memory_after = torch.cuda.memory_allocated() / (1024**3)
            memory_peak = torch.cuda.max_memory_allocated() / (1024**3)
            
            print(f"\n✅ SUCESSO! Imagem ultrawide gerada!")
            print(f"📁 Arquivo: {output_path}")
            print(f"⏱️ Tempo: {generation_time:.1f}s")
            print(f"📊 Memória GPU depois: {memory_after:.1f} GB")
            print(f"📊 Memória GPU pico: {memory_peak:.1f} GB")
            
            # Calcular eficiência
            mpixels = (WIDTH * HEIGHT) / 1000000
            speed = mpixels / generation_time
            print(f"🚀 Velocidade: {speed:.2f} megapixels/segundo")
            
            torch.cuda.reset_peak_memory_stats()
        
        print(f"\n🎯 RESULTADO:")
        print(f"✅ RTX 5070 consegue gerar {WIDTH}x{HEIGHT} (Ultrawide QHD)!")
        print(f"💡 Tempo razoável: {generation_time:.1f}s para {mpixels:.1f} megapixels")
        print(f"💡 Use esta resolução para paisagens cinematográficas!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Erro durante geração: {e}")
        
        # Verificar se é erro de VRAM
        if "out of memory" in str(e).lower() or "cuda" in str(e).lower():
            print("💾 Erro de memória GPU!")
            print("💡 Tente:")
            print("  - Menos steps (15-20)")
            print("  - Guidance scale menor (7.0)")
            print("  - Resolução menor (2560x1440)")
        
        return 1
    
    finally:
        # Cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


if __name__ == "__main__":
    sys.exit(test_ultrawide())
