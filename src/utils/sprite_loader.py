"""
Medieval Deck - Loader de Sprite Sheets

Carregador automático de sprite sheets e integração com sistema de animação.
"""

import pygame
from pathlib import Path
from typing import List, Dict, Optional
import logging

from ..gameplay.animation import animation_manager

logger = logging.getLogger(__name__)


def load_sprite_sheet(sheet_path: str, n_frames: int) -> List[pygame.Surface]:
    """
    Carrega sprite sheet e divide em frames individuais.
    
    Args:
        sheet_path: Caminho para o arquivo PNG do sprite sheet
        n_frames: Número de frames no sheet
        
    Returns:
        Lista de surfaces dos frames
    """
    try:
        # Carregar sprite sheet
        sheet_surface = pygame.image.load(sheet_path).convert_alpha()
        
        # Calcular dimensões de cada frame
        sheet_width = sheet_surface.get_width()
        sheet_height = sheet_surface.get_height()
        frame_width = sheet_width // n_frames
        
        # Extrair cada frame
        frames = []
        for i in range(n_frames):
            x = i * frame_width
            frame_rect = pygame.Rect(x, 0, frame_width, sheet_height)
            frame_surface = sheet_surface.subsurface(frame_rect).copy()
            frames.append(frame_surface)
            
        logger.debug(f"Carregado sprite sheet: {sheet_path} ({n_frames} frames)")
        return frames
        
    except Exception as e:
        logger.error(f"Erro ao carregar sprite sheet {sheet_path}: {e}")
        return []


def load_character_animations(char_id: str, sprite_sheets_dir: str = "assets/sprite_sheets") -> bool:
    """
    Carrega todas as animações de um personagem e registra no animation_manager.
    
    Args:
        char_id: ID do personagem
        sprite_sheets_dir: Diretório dos sprite sheets
        
    Returns:
        True se pelo menos uma animação foi carregada
    """
    sheets_path = Path(sprite_sheets_dir)
    loaded_count = 0
    
    # Ações padrão e número de frames
    action_frames = {
        "idle": 8,
        "attack": 12,
        "cast": 10,
        "hurt": 10,
        "death": 8
    }
    
    try:
        for action, n_frames in action_frames.items():
            sheet_file = sheets_path / f"{char_id}_{action}_sheet.png"
            
            if sheet_file.exists():
                frames = load_sprite_sheet(str(sheet_file), n_frames)
                
                if frames:
                    # Determinar se deve fazer loop
                    loop = action in ["idle"]  # Apenas idle faz loop
                    
                    # Registrar no animation manager
                    animation_manager.add_animation(
                        entity_id=char_id,
                        action=action,
                        frames=frames,
                        fps=30,
                        loop=loop
                    )
                    
                    loaded_count += 1
                    logger.debug(f"✅ Animação carregada: {char_id}_{action}")
                else:
                    logger.warning(f"❌ Falha ao carregar frames: {sheet_file}")
            else:
                logger.debug(f"Sprite sheet não encontrado: {sheet_file}")
                
        if loaded_count > 0:
            logger.info(f"Personagem {char_id}: {loaded_count} animações carregadas")
            return True
        else:
            logger.warning(f"Nenhuma animação encontrada para {char_id}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao carregar animações para {char_id}: {e}")
        return False


def load_all_character_animations(characters: List[str], sprite_sheets_dir: str = "assets/sprite_sheets") -> Dict[str, bool]:
    """
    Carrega animações para múltiplos personagens.
    
    Args:
        characters: Lista de IDs de personagens
        sprite_sheets_dir: Diretório dos sprite sheets
        
    Returns:
        Dicionário {char_id: success} indicando sucesso do carregamento
    """
    results = {}
    
    for char_id in characters:
        success = load_character_animations(char_id, sprite_sheets_dir)
        results[char_id] = success
        
    successful = sum(1 for success in results.values() if success)
    logger.info(f"Carregamento de animações: {successful}/{len(characters)} personagens")
    
    return results


def scale_animation_frames(char_id: str, action: str, target_height: int) -> bool:
    """
    Escala os frames de uma animação mantendo proporção.
    
    Args:
        char_id: ID do personagem
        action: Nome da ação
        target_height: Altura alvo em pixels
        
    Returns:
        True se escalou com sucesso
    """
    try:
        # Obter animação atual
        if char_id not in animation_manager.animations:
            return False
            
        if action not in animation_manager.animations[char_id]:
            return False
            
        animation = animation_manager.animations[char_id][action]
        original_frames = animation.frames
        
        if not original_frames:
            return False
            
        # Escalar cada frame
        scaled_frames = []
        for frame in original_frames:
            if frame.get_height() == 0:
                scaled_frames.append(frame)
                continue
                
            # Calcular nova largura mantendo proporção
            ratio = target_height / frame.get_height()
            new_width = int(frame.get_width() * ratio)
            
            # Escalar frame
            scaled_frame = pygame.transform.smoothscale(frame, (new_width, target_height))
            scaled_frames.append(scaled_frame)
            
        # Atualizar animação com frames escalados
        animation.frames = scaled_frames
        
        logger.debug(f"Frames escalados: {char_id}_{action} -> {target_height}px altura")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao escalar animação {char_id}_{action}: {e}")
        return False


def get_animation_frame_size(char_id: str, action: str) -> Optional[tuple]:
    """
    Retorna o tamanho (width, height) dos frames de uma animação.
    
    Args:
        char_id: ID do personagem
        action: Nome da ação
        
    Returns:
        Tupla (width, height) ou None se não encontrado
    """
    try:
        if char_id not in animation_manager.animations:
            return None
            
        if action not in animation_manager.animations[char_id]:
            return None
            
        animation = animation_manager.animations[char_id][action]
        if not animation.frames:
            return None
            
        first_frame = animation.frames[0]
        return (first_frame.get_width(), first_frame.get_height())
        
    except Exception as e:
        logger.error(f"Erro ao obter tamanho da animação {char_id}_{action}: {e}")
        return None
