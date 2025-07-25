"""
Funções utilitárias para interface do usuário.

Helpers para escalonamento, posicionamento e efeitos visuais.
"""

import pygame
from typing import Tuple


def fit_height(surface: pygame.Surface, target_h: int) -> pygame.Surface:
    """
    Redimensiona uma superficie mantendo proporção baseada na altura alvo.
    
    Args:
        surface: Superficie a ser redimensionada
        target_h: Altura alvo em pixels
        
    Returns:
        Superficie redimensionada com proporção mantida
    """
    if surface.get_height() == 0:
        return surface
        
    ratio = target_h / surface.get_height()
    new_width = int(surface.get_width() * ratio)
    new_size = (new_width, target_h)
    
    return pygame.transform.smoothscale(surface, new_size)


def fit_width(surface: pygame.Surface, target_w: int) -> pygame.Surface:
    """
    Redimensiona uma superficie mantendo proporção baseada na largura alvo.
    
    Args:
        surface: Superficie a ser redimensionada
        target_w: Largura alvo em pixels
        
    Returns:
        Superficie redimensionada com proporção mantida
    """
    if surface.get_width() == 0:
        return surface
        
    ratio = target_w / surface.get_width()
    new_height = int(surface.get_height() * ratio)
    new_size = (target_w, new_height)
    
    return pygame.transform.smoothscale(surface, new_size)


def create_gradient_surface(size: Tuple[int, int], color_top: Tuple[int, int, int], 
                          color_bottom: Tuple[int, int, int], alpha: int = 255) -> pygame.Surface:
    """
    Cria uma superficie com gradiente vertical.
    
    Args:
        size: Tamanho da superficie (width, height)
        color_top: Cor RGB do topo
        color_bottom: Cor RGB da base
        alpha: Transparência (0-255)
        
    Returns:
        Superficie com gradiente aplicado
    """
    surface = pygame.Surface(size, pygame.SRCALPHA)
    
    for y in range(size[1]):
        blend_factor = y / (size[1] - 1) if size[1] > 1 else 0
        
        r = int(color_top[0] * (1 - blend_factor) + color_bottom[0] * blend_factor)
        g = int(color_top[1] * (1 - blend_factor) + color_bottom[1] * blend_factor)
        b = int(color_top[2] * (1 - blend_factor) + color_bottom[2] * blend_factor)
        
        pygame.draw.line(surface, (r, g, b, alpha), (0, y), (size[0], y))
    
    return surface


def draw_outlined_text(surface: pygame.Surface, text: str, pos: Tuple[int, int], 
                      font: pygame.font.Font, text_color: Tuple[int, int, int],
                      outline_color: Tuple[int, int, int], outline_width: int = 2) -> pygame.Rect:
    """
    Desenha texto com contorno.
    
    Args:
        surface: Superficie onde desenhar
        text: Texto a ser desenhado
        pos: Posição (x, y)
        font: Fonte do texto
        text_color: Cor do texto RGB
        outline_color: Cor do contorno RGB
        outline_width: Espessura do contorno
        
    Returns:
        Retângulo ocupado pelo texto
    """
    # Desenhar contorno
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            outline_surf = font.render(text, True, outline_color)
            surface.blit(outline_surf, (pos[0] + dx, pos[1] + dy))
    
    # Desenhar texto principal
    text_surf = font.render(text, True, text_color)
    rect = surface.blit(text_surf, pos)
    
    return rect


def apply_glow_effect(surface: pygame.Surface, color: Tuple[int, int, int], 
                     glow_radius: int = 5) -> pygame.Surface:
    """
    Aplica efeito de brilho ao redor de uma superficie.
    
    Args:
        surface: Superficie original
        color: Cor do brilho RGB
        glow_radius: Raio do efeito de brilho
        
    Returns:
        Superficie com efeito de brilho aplicado
    """
    # Criar superficie maior para comportar o brilho
    expanded_size = (surface.get_width() + glow_radius * 2, 
                    surface.get_height() + glow_radius * 2)
    
    glow_surface = pygame.Surface(expanded_size, pygame.SRCALPHA)
    
    # Aplicar múltiplas camadas de brilho com transparência decrescente
    for i in range(glow_radius, 0, -1):
        alpha = int(80 * (glow_radius - i + 1) / glow_radius)
        glow_color = (*color, alpha)
        
        # Criar superficie temporária com a cor de brilho
        temp_surf = surface.copy()
        temp_surf.fill(glow_color, special_flags=pygame.BLEND_RGBA_MULT)
        
        # Desenhar em posições ligeiramente deslocadas
        for angle in range(0, 360, 45):  # 8 direções
            import math
            dx = int(math.cos(math.radians(angle)) * i)
            dy = int(math.sin(math.radians(angle)) * i)
            glow_surface.blit(temp_surf, (glow_radius + dx, glow_radius + dy))
    
    # Desenhar superficie original no centro
    glow_surface.blit(surface, (glow_radius, glow_radius))
    
    return glow_surface
