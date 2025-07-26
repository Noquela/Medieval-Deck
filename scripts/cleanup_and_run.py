#!/usr/bin/env python3
"""
Script para limpar assets antigos e executar o jogo com os novos assets gerados.
"""

import os
import shutil
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_old_assets():
    """Remove assets antigos das pastas obsoletas."""
    base_path = Path(__file__).parent.parent
    
    # Pastas de assets antigos para remover
    old_asset_folders = [
        "assets/ia",
        "assets/static",
        "assets/ui",
        "assets/characters",
        "assets/bg"
    ]
    
    removed_count = 0
    
    for folder in old_asset_folders:
        folder_path = base_path / folder
        if folder_path.exists():
            logger.info(f"🗑️  Removendo pasta antiga: {folder}")
            try:
                shutil.rmtree(folder_path)
                removed_count += 1
                logger.info(f"✅ Pasta removida: {folder}")
            except Exception as e:
                logger.error(f"❌ Erro ao remover {folder}: {e}")
        else:
            logger.info(f"📁 Pasta já não existe: {folder}")
    
    # Remover arquivos PNG antigos soltos na raiz de assets
    assets_root = base_path / "assets"
    if assets_root.exists():
        for png_file in assets_root.glob("*.png"):
            logger.info(f"🗑️  Removendo arquivo PNG antigo: {png_file.name}")
            try:
                png_file.unlink()
                removed_count += 1
                logger.info(f"✅ Arquivo removido: {png_file.name}")
            except Exception as e:
                logger.error(f"❌ Erro ao remover {png_file.name}: {e}")
    
    logger.info(f"🧹 Limpeza concluída! {removed_count} itens removidos.")
    return removed_count > 0

def verify_generated_assets():
    """Verifica se os assets gerados estão presentes."""
    base_path = Path(__file__).parent.parent
    generated_path = base_path / "assets" / "generated"
    
    if not generated_path.exists():
        logger.error("❌ Pasta assets/generated não encontrada!")
        return False
    
    # Assets essenciais que devem existir
    essential_assets = [
        "background.png",
        "knight_sprite.png", 
        "wizard_sprite.png",
        "button_texture_mystical.png",
        "button_texture_gold.png"
    ]
    
    missing_assets = []
    for asset in essential_assets:
        asset_path = generated_path / asset
        if not asset_path.exists():
            missing_assets.append(asset)
        else:
            logger.info(f"✅ Asset encontrado: {asset}")
    
    if missing_assets:
        logger.error(f"❌ Assets essenciais faltando: {missing_assets}")
        return False
    
    # Contar total de assets
    total_assets = len(list(generated_path.glob("*.png")))
    logger.info(f"📊 Total de assets gerados: {total_assets}")
    
    return True

def main():
    """Função principal."""
    logger.info("🚀 Iniciando limpeza e preparação para execução...")
    
    # 1. Verificar assets gerados
    if not verify_generated_assets():
        logger.error("❌ Assets gerados não estão prontos. Execute gen_assets_simple.py primeiro.")
        return False
    
    # 2. Limpar assets antigos
    cleanup_successful = cleanup_old_assets()
    
    # 3. Informar sobre a execução
    if cleanup_successful:
        logger.info("✅ Limpeza concluída! Assets antigos removidos.")
    
    logger.info("🎮 Pronto para executar o jogo com os novos assets!")
    logger.info("📝 Execute: python src/main.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Processo concluído com sucesso!")
        print("🎮 Agora você pode executar: python src/main.py")
    else:
        print("\n❌ Processo falhou. Verifique os logs acima.")
