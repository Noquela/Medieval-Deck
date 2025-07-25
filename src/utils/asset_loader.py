"""
Sistema de carregamento automático de assets gerados por IA.

Detecta e carrega recursivamente todos os assets da pasta `assets/ia/`
sem necessidade de paths hardcoded, seguindo convenções de nomenclatura.
"""

import os
import pygame
import logging
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AssetInfo:
    """Informações de um asset carregado."""
    name: str
    path: str
    surface: pygame.Surface
    category: str  # background, sprite, button, icon, etc.
    variant: str   # idle, hover, pressed, etc.


class AssetLoader:
    """
    Carregador automático de assets IA com descoberta recursiva.
    
    Convenções de nomenclatura:
    - Backgrounds: menu_bg.png, knight_bg.png, wizard_bg.png, assassin_bg.png
    - Sprites: knight_sprite.png, wizard_sprite.png, assassin_sprite.png  
    - Botões: button_idle.png, button_hover.png, button_pressed.png
    - Ícones: icon_arrow_left.png, icon_arrow_right.png
    - UI: frame_ornate.png, scroll_texture.png, etc.
    """
    
    def __init__(self, assets_dir: str = "assets/ia"):
        self.assets_dir = Path(assets_dir)
        self.assets: Dict[str, AssetInfo] = {}
        self.categories: Dict[str, List[AssetInfo]] = {}
        
        # Garantir que pygame está inicializado
        if not pygame.get_init():
            pygame.init()
            
        logger.info(f"AssetLoader inicializado para: {self.assets_dir}")
    
    def load_all_assets(self) -> Dict[str, AssetInfo]:
        """
        Carrega todos os assets da pasta IA recursivamente.
        
        Returns:
            Dicionário com assets carregados {nome: AssetInfo}
        """
        self.assets.clear()
        self.categories.clear()
        
        if not self.assets_dir.exists():
            logger.warning(f"Diretório de assets não encontrado: {self.assets_dir}")
            # Criar diretório se não existir
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            return self.assets
            
        # Descobrir recursivamente todos os arquivos de imagem
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tga'}
        
        for file_path in self.assets_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                self._load_single_asset(file_path)
        
        # Organizar por categorias
        self._organize_by_categories()
        
        logger.info(f"Carregados {len(self.assets)} assets em {len(self.categories)} categorias")
        return self.assets
    
    def _load_single_asset(self, file_path: Path) -> Optional[AssetInfo]:
        """
        Carrega um único asset e determina sua categoria/variante.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            AssetInfo se carregado com sucesso
        """
        try:
            # Carregar imagem
            surface = pygame.image.load(str(file_path)).convert_alpha()
            
            # Extrair informações do nome do arquivo
            name = file_path.stem  # nome sem extensão
            category, variant = self._parse_asset_name(name)
            
            asset_info = AssetInfo(
                name=name,
                path=str(file_path),
                surface=surface,
                category=category,
                variant=variant
            )
            
            self.assets[name] = asset_info
            logger.debug(f"Asset carregado: {name} ({category}/{variant}) - {surface.get_size()}")
            
            return asset_info
            
        except Exception as e:
            logger.error(f"Erro ao carregar asset {file_path}: {e}")
            return None
    
    def _parse_asset_name(self, name: str) -> tuple[str, str]:
        """
        Extrai categoria e variante do nome do asset.
        
        Args:
            name: Nome do asset (sem extensão)
            
        Returns:
            Tupla (categoria, variante)
        """
        # Mapear padrões de nomes para categorias
        if name.endswith('_bg'):
            return 'background', name.replace('_bg', '')
        elif name.endswith('_sprite'):
            return 'sprite', name.replace('_sprite', '')
        elif name.startswith('button_'):
            return 'button', name.replace('button_', '')
        elif name.startswith('icon_'):
            return 'icon', name.replace('icon_', '')
        elif 'menu' in name and 'bg' in name:
            return 'background', 'menu'
        elif 'cinematic' in name:
            return 'cinematic', name.replace('_cinematic', '')
        elif 'frame' in name:
            return 'ui', 'frame'
        elif 'scroll' in name:
            return 'ui', 'scroll'
        elif 'texture' in name:
            return 'texture', name.replace('_texture', '')
        else:
            # Categoria genérica
            return 'misc', name
    
    def _organize_by_categories(self):
        """Organiza assets por categorias para busca eficiente."""
        for asset in self.assets.values():
            if asset.category not in self.categories:
                self.categories[asset.category] = []
            self.categories[asset.category].append(asset)
    
    def get_asset(self, name: str) -> Optional[pygame.Surface]:
        """
        Obtém surface de um asset pelo nome.
        
        Args:
            name: Nome do asset
            
        Returns:
            Surface do pygame ou None se não encontrado
        """
        asset_info = self.assets.get(name)
        return asset_info.surface if asset_info else None
    
    def get_assets_by_category(self, category: str) -> List[AssetInfo]:
        """
        Obtém todos os assets de uma categoria.
        
        Args:
            category: Categoria (background, sprite, button, etc.)
            
        Returns:
            Lista de AssetInfo da categoria
        """
        return self.categories.get(category, [])
    
    def get_button_states(self) -> Dict[str, pygame.Surface]:
        """
        Obtém todos os estados de botões (idle, hover, pressed).
        
        Returns:
            Dicionário {estado: surface}
        """
        button_assets = self.get_assets_by_category('button')
        states = {}
        
        for asset in button_assets:
            states[asset.variant] = asset.surface
            
        # Garantir estados padrão
        if 'idle' not in states and button_assets:
            states['idle'] = button_assets[0].surface
        if 'hover' not in states:
            states['hover'] = states.get('idle')
        if 'pressed' not in states:
            states['pressed'] = states.get('idle')
            
        return states
    
    def get_character_assets(self, character: str) -> Dict[str, pygame.Surface]:
        """
        Obtém todos os assets relacionados a um personagem.
        
        Args:
            character: Nome do personagem (knight, wizard, assassin)
            
        Returns:
            Dicionário {tipo: surface} (bg, sprite, etc.)
        """
        assets = {}
        
        # Background
        bg_asset = self.get_asset(f"{character}_bg")
        if bg_asset:
            assets['background'] = bg_asset
            
        # Sprite
        sprite_asset = self.get_asset(f"{character}_sprite")
        if sprite_asset:
            assets['sprite'] = sprite_asset
            
        # Cinematográfico
        cinematic_asset = self.get_asset(f"{character}_cinematic")
        if cinematic_asset:
            assets['cinematic'] = cinematic_asset
            
        return assets
    
    def list_available_assets(self) -> Dict[str, List[str]]:
        """
        Lista todos os assets disponíveis organizados por categoria.
        
        Returns:
            Dicionário {categoria: [nomes]}
        """
        result = {}
        for category, assets in self.categories.items():
            result[category] = [asset.name for asset in assets]
        return result


# Instância global do carregador
asset_loader = AssetLoader()


def load_ia_assets(assets_dir: str = "assets/ia") -> Dict[str, pygame.Surface]:
    """
    Função de conveniência para carregar todos os assets IA.
    
    Args:
        assets_dir: Diretório dos assets IA
        
    Returns:
        Dicionário {nome: surface} de todos os assets
    """
    global asset_loader
    asset_loader = AssetLoader(assets_dir)
    all_assets = asset_loader.load_all_assets()
    
    # Retornar apenas as surfaces para compatibilidade
    return {name: info.surface for name, info in all_assets.items()}


def get_asset(name: str) -> Optional[pygame.Surface]:
    """
    Função de conveniência para obter um asset.
    
    Args:
        name: Nome do asset
        
    Returns:
        Surface do pygame ou None
    """
    return asset_loader.get_asset(name)


def get_button_states() -> Dict[str, pygame.Surface]:
    """
    Função de conveniência para obter estados de botões.
    
    Returns:
        Dicionário {estado: surface}
    """
    return asset_loader.get_button_states()


def get_character_assets(character: str) -> Dict[str, pygame.Surface]:
    """
    Função de conveniência para obter assets de personagem.
    
    Args:
        character: Nome do personagem
        
    Returns:
        Dicionário {tipo: surface}
    """
    return asset_loader.get_character_assets(character)
