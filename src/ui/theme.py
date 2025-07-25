"""
Medieval Deck UI Theme System

Paleta de cores, tipografia e constantes visuais para o jogo.
Inspirado em designs cinematográficos medievais com tons dourados, púrpura e pedra.
"""

import pygame
from typing import Dict, Tuple, NamedTuple
from pathlib import Path

class ColorPalette(NamedTuple):
    """Paleta de cores medieval cinematográfica."""
    # Cores primárias
    GOLD_PRIMARY: Tuple[int, int, int] = (218, 165, 32)     # Dourado principal
    GOLD_LIGHT: Tuple[int, int, int] = (255, 215, 0)        # Dourado claro
    GOLD_DARK: Tuple[int, int, int] = (184, 134, 11)        # Dourado escuro
    
    # Cores secundárias
    PURPLE_MYSTICAL: Tuple[int, int, int] = (75, 0, 130)    # Púrpura místico
    PURPLE_LIGHT: Tuple[int, int, int] = (138, 43, 226)     # Púrpura claro
    
    GREEN_FOREST: Tuple[int, int, int] = (34, 139, 34)      # Verde floresta
    GREEN_DARK: Tuple[int, int, int] = (0, 100, 0)          # Verde escuro
    
    # Tons neutros medievais
    STONE_LIGHT: Tuple[int, int, int] = (169, 169, 169)     # Pedra clara
    STONE_MEDIUM: Tuple[int, int, int] = (105, 105, 105)    # Pedra média
    STONE_DARK: Tuple[int, int, int] = (47, 47, 47)         # Pedra escura
    
    # Tons especiais
    BLOOD_RED: Tuple[int, int, int] = (139, 0, 0)           # Vermelho sangue
    SHADOW_BLACK: Tuple[int, int, int] = (25, 25, 25)       # Preto sombra
    PARCHMENT: Tuple[int, int, int] = (245, 245, 220)       # Pergaminho
    
    # Estados de UI
    SUCCESS: Tuple[int, int, int] = (0, 255, 0)             # Verde sucesso
    WARNING: Tuple[int, int, int] = (255, 255, 0)           # Amarelo aviso
    ERROR: Tuple[int, int, int] = (255, 0, 0)               # Vermelho erro
    
    # Transparências
    OVERLAY_DARK: Tuple[int, int, int, int] = (0, 0, 0, 128)        # Sobreposição escura
    OVERLAY_LIGHT: Tuple[int, int, int, int] = (255, 255, 255, 64)  # Sobreposição clara
    GLOW_GOLD: Tuple[int, int, int, int] = (255, 215, 0, 80)        # Brilho dourado


class Typography:
    """Sistema de tipografia medieval."""
    
    def __init__(self):
        self.fonts: Dict[str, pygame.font.Font] = {}
        self._fonts_loaded = False
    
    def _load_fonts(self):
        """Carrega fontes do sistema e personalizadas (lazy loading)."""
        if self._fonts_loaded:
            return
            
        try:
            # Verificar se pygame está inicializado
            if not pygame.get_init():
                pygame.init()
                pygame.font.init()
                
            # Fontes serifadas para títulos (estilo medieval)
            self.fonts['title_large'] = pygame.font.Font(None, 72)
            self.fonts['title_medium'] = pygame.font.Font(None, 48)
            self.fonts['title_small'] = pygame.font.Font(None, 36)
            
            # Fontes sans-serif para corpo (legibilidade)
            self.fonts['body_large'] = pygame.font.Font(None, 32)
            self.fonts['body_medium'] = pygame.font.Font(None, 24)
            self.fonts['body_small'] = pygame.font.Font(None, 18)
            
            # Fontes especiais
            self.fonts['button'] = pygame.font.Font(None, 28)
            self.fonts['label'] = pygame.font.Font(None, 20)
            
            self._fonts_loaded = True
            
        except Exception as e:
            print(f"Erro ao carregar fontes: {e}")
            # Fallback para fonte padrão
            try:
                default_font = pygame.font.Font(None, 24)
                for key in ['title_large', 'title_medium', 'title_small', 
                           'body_large', 'body_medium', 'body_small', 'button', 'label']:
                    self.fonts[key] = default_font
                self._fonts_loaded = True
            except:
                # Última tentativa com dicionário vazio
                self._fonts_loaded = True
    
    def get_font(self, font_type: str) -> pygame.font.Font:
        """Retorna fonte do tipo especificado."""
        if not self._fonts_loaded:
            self._load_fonts()
        return self.fonts.get(font_type, self.fonts.get('body_medium'))


class Spacing:
    """Constantes de espaçamento e dimensões."""
    
    # Margens e padding
    PADDING_TINY = 4
    PADDING_SMALL = 8
    PADDING_MEDIUM = 16
    PADDING_LARGE = 24
    PADDING_HUGE = 32
    
    # Bordas e raios
    BORDER_RADIUS_SMALL = 4
    BORDER_RADIUS_MEDIUM = 8
    BORDER_RADIUS_LARGE = 12
    BORDER_RADIUS_HUGE = 16
    
    # Sombras
    SHADOW_OFFSET_SMALL = 2
    SHADOW_OFFSET_MEDIUM = 4
    SHADOW_OFFSET_LARGE = 8
    SHADOW_BLUR_SMALL = 4
    SHADOW_BLUR_MEDIUM = 8
    SHADOW_BLUR_LARGE = 16
    
    # Animações
    ANIMATION_FAST = 100      # ms
    ANIMATION_MEDIUM = 200    # ms
    ANIMATION_SLOW = 400      # ms
    ANIMATION_VERY_SLOW = 800 # ms


class Theme:
    """Tema principal do Medieval Deck."""
    
    def __init__(self):
        self.colors = ColorPalette()
        self.typography = Typography()
        self.spacing = Spacing()
        
        # Configurações de performance
        self.enable_particles = True
        self.enable_glow_effects = True
        self.enable_shadows = True
        self.animation_quality = "high"  # "low", "medium", "high"
    
    def set_performance_mode(self, mode: str):
        """
        Ajusta qualidade visual baseado na performance.
        
        Args:
            mode: "low", "medium", "high"
        """
        if mode == "low":
            self.enable_particles = False
            self.enable_glow_effects = False
            self.enable_shadows = False
            self.animation_quality = "low"
        elif mode == "medium":
            self.enable_particles = True
            self.enable_glow_effects = False
            self.enable_shadows = True
            self.animation_quality = "medium"
        else:  # high
            self.enable_particles = True
            self.enable_glow_effects = True
            self.enable_shadows = True
            self.animation_quality = "high"


# Instância global do tema
theme = Theme()


def draw_text_with_shadow(surface: pygame.Surface, text: str, font: pygame.font.Font,
                         pos: Tuple[int, int], color: Tuple[int, int, int],
                         shadow_color: Tuple[int, int, int] = (0, 0, 0),
                         shadow_offset: Tuple[int, int] = (2, 2)) -> pygame.Rect:
    """
    Desenha texto com sombra projetada.
    
    Args:
        surface: Superfície de destino
        text: Texto a desenhar
        font: Fonte a usar
        pos: Posição (x, y)
        color: Cor do texto
        shadow_color: Cor da sombra
        shadow_offset: Deslocamento da sombra (x, y)
    
    Returns:
        Retângulo do texto desenhado
    """
    if theme.enable_shadows:
        # Desenha sombra
        shadow_surf = font.render(text, True, shadow_color)
        shadow_pos = (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1])
        surface.blit(shadow_surf, shadow_pos)
    
    # Desenha texto principal
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, pos)
    
    return text_surf.get_rect(topleft=pos)


def create_gradient_surface(size: Tuple[int, int], 
                          color_top: Tuple[int, int, int],
                          color_bottom: Tuple[int, int, int]) -> pygame.Surface:
    """
    Cria superfície com gradiente vertical.
    
    Args:
        size: Tamanho (largura, altura)
        color_top: Cor superior
        color_bottom: Cor inferior
    
    Returns:
        Superfície com gradiente
    """
    surface = pygame.Surface(size)
    
    for y in range(size[1]):
        # Interpola entre as cores
        ratio = y / size[1]
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        
        pygame.draw.line(surface, (r, g, b), (0, y), (size[0], y))
    
    return surface


def create_glow_surface(size: Tuple[int, int], 
                       color: Tuple[int, int, int],
                       intensity: float = 0.3) -> pygame.Surface:
    """
    Cria superfície com efeito de brilho.
    
    Args:
        size: Tamanho da superfície
        color: Cor do brilho
        intensity: Intensidade do brilho (0.0 a 1.0)
    
    Returns:
        Superfície com efeito de brilho
    """
    if not theme.enable_glow_effects:
        return pygame.Surface(size, pygame.SRCALPHA)
    
    surface = pygame.Surface(size, pygame.SRCALPHA)
    center_x, center_y = size[0] // 2, size[1] // 2
    max_radius = min(center_x, center_y)
    
    for radius in range(max_radius, 0, -1):
        alpha = int(255 * intensity * (radius / max_radius))
        glow_color = (*color, alpha)
        pygame.draw.circle(surface, glow_color, (center_x, center_y), radius)
    
    return surface
