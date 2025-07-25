"""
Teste de Geração de Imagens HD/4K
Testa diferentes resoluções para ver o que a RTX 5070 consegue gerar.
"""

import sys
import logging
import torch
from pathlib import Path
from typing import Dict, List, Tuple
import time

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.utils.config import Config
from src.utils.helpers import setup_logging, get_system_info
from src.models.sdxl_pipeline import SDXLPipeline

# Test resolutions
RESOLUTIONS = [
    ("1024x1024", 1024, 1024),    # Standard SDXL
    ("1280x720", 1280, 720),      # HD 720p
    ("1920x1080", 1920, 1080),    # Full HD 1080p
    ("2560x1440", 2560, 1440),    # QHD 1440p
    ("3840x2160", 3840, 2160),    # 4K UHD
]

TEST_PROMPT = """masterpiece, high quality, detailed, medieval fantasy castle on hilltop, 
dramatic sunset lighting, gothic architecture, stone walls, towers with flags, 
atmospheric clouds, cinematic composition, photorealistic"""

NEGATIVE_PROMPT = """blurry, low quality, pixelated, distorted, ugly, deformed, 
watermark, text, signature, artist name"""


def test_memory_requirements():
    """Testa os requisitos de memória da GPU."""
    print("🔍 Verificando memória GPU disponível...")
    
    if torch.cuda.is_available():
        device = torch.cuda.current_device()
        gpu_memory = torch.cuda.get_device_properties(device).total_memory
        gpu_memory_gb = gpu_memory / (1024**3)
        
        free_memory = torch.cuda.mem_get_info()[0]
        free_memory_gb = free_memory / (1024**3)
        
        print(f"📊 GPU: {torch.cuda.get_device_name(device)}")
        print(f"💾 Memória Total: {gpu_memory_gb:.1f} GB")
        print(f"🆓 Memória Livre: {free_memory_gb:.1f} GB")
        
        return gpu_memory_gb, free_memory_gb
    else:
        print("❌ CUDA não disponível")
        return 0, 0


def estimate_vram_usage(width: int, height: int) -> float:
    """
    Estima o uso de VRAM para uma resolução específica.
    Baseado em fórmulas empíricas para SDXL.
    """
    # Base VRAM para SDXL (modelo + overhead)
    base_vram = 6.5  # GB
    
    # VRAM adicional baseado na resolução
    pixels = width * height
    base_pixels = 1024 * 1024  # Resolução padrão SDXL
    
    # Fator de escala para VRAM (não linear)
    scale_factor = (pixels / base_pixels) ** 0.8
    additional_vram = (scale_factor - 1) * 2.5  # GB
    
    return base_vram + additional_vram


def test_resolution(
    pipeline: SDXLPipeline,
    name: str,
    width: int,
    height: int,
    output_dir: Path
) -> Dict:
    """Testa uma resolução específica."""
    print(f"\n🎯 Testando resolução: {name} ({width}x{height})")
    
    # Estimar VRAM necessário
    estimated_vram = estimate_vram_usage(width, height)
    print(f"📊 VRAM estimado necessário: {estimated_vram:.1f} GB")
    
    # Limpar cache da GPU
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    start_time = time.time()
    success = False
    error_msg = None
    output_path = None
    
    try:
        # Gerar imagem
        print(f"🎨 Gerando imagem {width}x{height}...")
        
        result = pipeline.generate_image(
            prompt=TEST_PROMPT,
            negative_prompt=NEGATIVE_PROMPT,
            width=width,
            height=height,
            num_inference_steps=50,  # Reduzido para teste mais rápido
            guidance_scale=8.5
        )
        
        if result and result.get("success"):
            # Salvar imagem
            output_path = output_dir / f"test_{name.lower().replace('x', '_')}.png"
            
            # A imagem está em result["image"]
            image = result["image"]
            image.save(output_path)
            
            success = True
            print(f"✅ Sucesso! Imagem salva em: {output_path}")
            
        else:
            error_msg = result.get("error", "Erro desconhecido na geração")
            print(f"❌ Falha: {error_msg}")
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Erro durante geração: {error_msg}")
        
        # Verificar se é erro de VRAM
        if "out of memory" in error_msg.lower() or "cuda" in error_msg.lower():
            print("💾 Erro de memória GPU detectado")
    
    end_time = time.time()
    generation_time = end_time - start_time
    
    # Verificar memória após geração
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        memory_used = torch.cuda.max_memory_allocated() / (1024**3)
        print(f"📊 Memória GPU usada: {memory_used:.1f} GB")
        torch.cuda.reset_peak_memory_stats()
    else:
        memory_used = 0
    
    return {
        "resolution": name,
        "width": width,
        "height": height,
        "success": success,
        "error": error_msg,
        "generation_time": generation_time,
        "estimated_vram": estimated_vram,
        "actual_vram": memory_used,
        "output_path": str(output_path) if output_path else None
    }


def main():
    """Função principal do teste."""
    print("🏰 Medieval Deck - Teste de Geração HD/4K")
    print("=" * 50)
    
    # Setup logging
    setup_logging(level="INFO")
    
    # Verificar sistema
    print("\n🔍 Informações do Sistema:")
    system_info = get_system_info()
    print(f"GPU: {system_info.get('cuda', {}).get('device_name', 'N/A')}")
    
    # Verificar memória
    total_gpu_memory, free_gpu_memory = test_memory_requirements()
    
    if total_gpu_memory < 12:
        print(f"⚠️ Aviso: GPU com {total_gpu_memory:.1f} GB pode ter limitações para 4K")
    
    # Criar diretório de output
    output_dir = Path("test_hd_outputs")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Inicializar configuração
        config = Config()
        
        # Inicializar pipeline SDXL
        print("\n🚀 Inicializando pipeline SDXL...")
        pipeline = SDXLPipeline(
            model_id=config.ai.model_id,
            refiner_id=config.ai.refiner_id,
            enable_refiner=False,  # Desabilitar refiner para economizar VRAM
            device=config.get_device(),
            cache_dir=str(config.assets_cache_dir),
            memory_efficient=True
        )
        
        print("✅ Pipeline inicializado com sucesso!")
        
        # Testar resoluções
        results = []
        for name, width, height in RESOLUTIONS:
            # Verificar se vale a pena tentar
            estimated_vram = estimate_vram_usage(width, height)
            if estimated_vram > free_gpu_memory * 1.2:  # Margem de segurança
                print(f"\n⏭️ Pulando {name}: VRAM estimado ({estimated_vram:.1f} GB) > disponível ({free_gpu_memory:.1f} GB)")
                continue
            
            result = test_resolution(pipeline, name, width, height, output_dir)
            results.append(result)
            
            # Se falhou por memória, parar testes maiores
            if not result["success"] and result.get("error") and "memory" in result["error"].lower():
                print("\n🛑 Parando testes - limite de memória atingido")
                break
        
        # Relatório final
        print("\n" + "=" * 50)
        print("📊 RELATÓRIO FINAL")
        print("=" * 50)
        
        successful_resolutions = []
        for result in results:
            status = "✅ SUCESSO" if result["success"] else "❌ FALHA"
            print(f"\n{result['resolution']}: {status}")
            print(f"  Tempo: {result['generation_time']:.1f}s")
            print(f"  VRAM estimado: {result['estimated_vram']:.1f} GB")
            print(f"  VRAM usado: {result['actual_vram']:.1f} GB")
            
            if result["success"]:
                successful_resolutions.append(result["resolution"])
                print(f"  Arquivo: {result['output_path']}")
            else:
                print(f"  Erro: {result['error']}")
        
        # Recomendações
        print(f"\n🎯 RECOMENDAÇÕES:")
        if successful_resolutions:
            max_resolution = successful_resolutions[-1]
            print(f"✅ Resolução máxima suportada: {max_resolution}")
            
            if "4K" in max_resolution or "3840x2160" in max_resolution:
                print("🔥 Excelente! Sua GPU suporta geração 4K!")
            elif "1920x1080" in max_resolution:
                print("👍 Ótimo! Sua GPU suporta Full HD!")
            elif "1280x720" in max_resolution:
                print("👌 Sua GPU suporta HD 720p")
            
            print(f"💡 Para melhor performance, use: {successful_resolutions[-1]}")
            print(f"💡 Para qualidade máxima, use: {successful_resolutions[-1]} com refiner")
        else:
            print("❌ Nenhuma resolução HD foi suportada")
            print("💡 Tente reduzir outras configurações ou usar modo memory_efficient")
        
        print(f"\n📁 Imagens geradas salvas em: {output_dir.absolute()}")
        
    except Exception as e:
        print(f"\n❌ Erro fatal no teste: {e}")
        logging.error(f"Erro no teste HD: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
