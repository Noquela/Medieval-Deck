"""
Teste simples de geração HD/4K
Corrige o erro do teste anterior e testa diferentes resoluções.
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

# Test resolutions
RESOLUTIONS = [
    ("1024x1024", 1024, 1024),    # Standard SDXL
    ("1920x1080", 1920, 1080),    # Full HD
    ("2560x1440", 2560, 1440),    # QHD
]

TEST_PROMPT = """masterpiece, high quality, detailed, medieval fantasy castle on hilltop, 
dramatic sunset lighting, gothic architecture, stone walls, towers with flags, 
atmospheric clouds, cinematic composition"""

NEGATIVE_PROMPT = """blurry, low quality, pixelated, distorted, ugly, deformed"""


def test_resolution_simple(pipeline, name, width, height, output_dir):
    """Teste simplificado de uma resolução."""
    print(f"\n🎯 Testando {name} ({width}x{height})")
    
    # Limpar cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        
        # Memória antes
        memory_before = torch.cuda.memory_allocated() / (1024**3)
        print(f"📊 Memória GPU antes: {memory_before:.1f} GB")
    
    start_time = time.time()
    success = False
    output_path = None
    error_msg = None
    
    try:
        # Gerar imagem
        print(f"🎨 Gerando imagem...")
        
        # Usar o método generate_image da classe SDXLPipeline
        image = pipeline.generate_image(
            prompt=TEST_PROMPT,
            negative_prompt=NEGATIVE_PROMPT,
            width=width,
            height=height,
            num_inference_steps=30,  # Reduzido para teste mais rápido
            guidance_scale=8.5
        )
        
        # Salvar imagem
        output_path = output_dir / f"test_{name.lower().replace('x', '_')}.png"
        image.save(output_path)
        
        success = True
        print(f"✅ Sucesso! Imagem salva: {output_path}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erro: {error_msg}")
        
        # Verificar se é erro de VRAM
        if "out of memory" in error_msg.lower() or "cuda" in error_msg.lower():
            print("💾 Erro de memória GPU!")
    
    end_time = time.time()
    generation_time = end_time - start_time
    
    # Memória após
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        memory_after = torch.cuda.memory_allocated() / (1024**3)
        memory_peak = torch.cuda.max_memory_allocated() / (1024**3)
        print(f"📊 Memória GPU depois: {memory_after:.1f} GB")
        print(f"📊 Memória GPU pico: {memory_peak:.1f} GB")
        torch.cuda.reset_peak_memory_stats()
    
    print(f"⏱️ Tempo: {generation_time:.1f}s")
    
    return {
        "resolution": name,
        "width": width,
        "height": height,
        "success": success,
        "error": error_msg,
        "time": generation_time,
        "output_path": str(output_path) if output_path else None
    }


def main():
    """Função principal do teste simplificado."""
    print("🏰 Medieval Deck - Teste HD/4K Simplificado")
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
    
    # Criar diretório de output
    output_dir = Path("test_hd_simple")
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
        
        # Testar resoluções
        results = []
        
        for name, width, height in RESOLUTIONS:
            result = test_resolution_simple(pipeline, name, width, height, output_dir)
            results.append(result)
            
            # Se falhou por memória, parar
            if not result["success"] and result.get("error") and "memory" in result["error"].lower():
                print(f"\n🛑 Parando testes - erro de memória")
                break
        
        # Relatório final
        print(f"\n" + "=" * 50)
        print("📊 RESULTADOS FINAIS")
        print("=" * 50)
        
        successful = []
        for result in results:
            status = "✅ SUCESSO" if result["success"] else "❌ FALHA"
            print(f"\n{result['resolution']}: {status}")
            print(f"  ⏱️ Tempo: {result['time']:.1f}s")
            
            if result["success"]:
                successful.append(result["resolution"])
                print(f"  📁 Arquivo: {result['output_path']}")
            else:
                print(f"  ❌ Erro: {result['error']}")
        
        # Recomendações
        print(f"\n🎯 RECOMENDAÇÕES:")
        if successful:
            print(f"✅ Resoluções que funcionaram: {', '.join(successful)}")
            
            max_res = successful[-1]
            if "2560x1440" in max_res:
                print("🔥 EXCELENTE! Sua RTX 5070 suporta QHD (1440p)!")
            elif "1920x1080" in max_res:
                print("👍 ÓTIMO! Sua RTX 5070 suporta Full HD!")
            elif "1024x1024" in max_res:
                print("👌 Funciona com resolução padrão SDXL")
                
            print(f"💡 Use {max_res} para melhor qualidade")
            print(f"💡 Para 4K, pode precisar de menos steps ou desabilitar refiner")
        else:
            print("❌ Algo deu errado - nenhuma resolução funcionou")
        
        print(f"\n📁 Imagens salvas em: {output_dir.absolute()}")
        
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
