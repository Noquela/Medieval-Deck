"""
Utilitários para processamento de assets e sprites.

Funções para redimensionamento, escalonamento e manipulação de imagens
no Medieval Deck.
"""

import pygame
from typing import Tuple, Optional


def fit_height(surface: pygame.Surface, target_height: int) -> pygame.Surface:
    """
    Redimensiona uma surface mantendo a proporção para uma altura específica.
    
    Args:
        surface: Surface original do Pygame
        target_height: Altura desejada em pixels
        
    Returns:
        Surface redimensionada mantendo proporção
    """
    if not surface:
        return surface
        
    original_width, original_height = surface.get_size()
    
    if original_height == 0:
        return surface
        
    # Calcular nova largura mantendo proporção
    scale_factor = target_height / original_height
    new_width = int(original_width * scale_factor)
    
    # Redimensionar com suavização
    return pygame.transform.smoothscale(surface, (new_width, target_height))


def fit_width(surface: pygame.Surface, target_width: int) -> pygame.Surface:
    """
    Redimensiona uma surface mantendo a proporção para uma largura específica.
    
    Args:
        surface: Surface original do Pygame
        target_width: Largura desejada em pixels
        
    Returns:
        Surface redimensionada mantendo proporção
    """
    if not surface:
        return surface
        
    original_width, original_height = surface.get_size()
    
    if original_width == 0:
        return surface
        
    # Calcular nova altura mantendo proporção
    scale_factor = target_width / original_width
    new_height = int(original_height * scale_factor)
    
    # Redimensionar com suavização
    return pygame.transform.smoothscale(surface, (target_width, new_height))


def fit_size(surface: pygame.Surface, target_size: Tuple[int, int], 
             maintain_aspect: bool = True) -> pygame.Surface:
    """
    Redimensiona uma surface para um tamanho específico.
    
    Args:
        surface: Surface original do Pygame
        target_size: Tupla (largura, altura) desejada
        maintain_aspect: Se deve manter a proporção (padrão: True)
        
    Returns:
        Surface redimensionada
    """
    if not surface:
        return surface
        
    if maintain_aspect:
        # Escolher o menor fator de escala para caber na área
        original_width, original_height = surface.get_size()
        target_width, target_height = target_size
        
        scale_w = target_width / original_width
        scale_h = target_height / original_height
        scale = min(scale_w, scale_h)
        
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        
        return pygame.transform.smoothscale(surface, (new_width, new_height))
    else:
        # Esticar para caber exatamente
        return pygame.transform.smoothscale(surface, target_size)


def center_surface_in_rect(surface: pygame.Surface, rect: pygame.Rect) -> Tuple[int, int]:
    """
    Calcula a posição para centralizar uma surface dentro de um retângulo.
    
    Args:
        surface: Surface a ser centralizada
        rect: Retângulo alvo
        
    Returns:
        Tupla (x, y) para posição centralizada
    """
    if not surface:
        return rect.x, rect.y
        
    surface_rect = surface.get_rect()
    surface_rect.center = rect.center
    return surface_rect.x, surface_rect.y


def create_outline_surface(surface: pygame.Surface, outline_color: Tuple[int, int, int], 
                          outline_width: int = 2) -> pygame.Surface:
    """
    Cria uma surface com outline (contorno) colorido.
    
    Args:
        surface: Surface original
        outline_color: Cor do contorno RGB
        outline_width: Espessura do contorno em pixels
        
    Returns:
        Nova surface com contorno
    """
    if not surface:
        return surface
        
    original_size = surface.get_size()
    new_size = (original_size[0] + outline_width * 2, 
                original_size[1] + outline_width * 2)
    
    # Criar surface com transparência
    outlined_surface = pygame.Surface(new_size, pygame.SRCALPHA)
    
    # Desenhar outline em todas as direções
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:  # Não desenhar no centro
                # Criar máscara colorida
                mask_surface = surface.copy()
                mask_surface.fill(outline_color, special_flags=pygame.BLEND_MULT)
                
                # Desenhar na posição offset
                outlined_surface.blit(mask_surface, 
                                    (outline_width + dx, outline_width + dy))
    
    # Desenhar surface original por cima
    outlined_surface.blit(surface, (outline_width, outline_width))
    
    return outlined_surface
