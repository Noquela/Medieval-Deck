"""
Medieval Deck - Theme Configuration

Centraliza cores, fontes e constantes visuais para o MVP.
"""

import pygame
from pathlib import Path
from typing import Dict, Tuple

class Theme:
    """Configuração visual centralizada do Medieval Deck."""
    
    # === CORES ===
    COLORS = {
        # Principais
        "gold": (212, 180, 106),
        "gold_dark": (180, 150, 80),
        "silver": (192, 192, 192),
        
        # Status
        "hp": (220, 68, 58),
        "hp_dark": (180, 40, 30),
        "mana": (39, 131, 221),
        "mana_dark": (20, 80, 160),
        "block": (150, 150, 150),
        
        # UI
        "ui_mask": (18, 11, 5, 140),
        "text_light": (245, 240, 230),
        "text_dark": (40, 30, 20),
        "background": (25, 20, 15),
        
        # Cards
        "card_attack": (220, 68, 58),
        "card_defense": (150, 150, 150),
        "card_magic": (39, 131, 221),
        "card_heal": (68, 220, 68),
        
        # Effects
        "glow_gold": (255, 215, 0, 128),
        "particles_hit": (255, 100, 100),
        "particles_heal": (100, 255, 100),
        "particles_magic": (100, 100, 255),
    }
    
    # === FONTES ===
    @classmethod
    def init_fonts(cls):
        """Inicializa as fontes do tema."""
        try:
            # Fontes principais (se disponíveis)
            cls.FONT_TITLE = pygame.font.Font(None, 32)  # Placeholder
            cls.FONT_SUBTITLE = pygame.font.Font(None, 24)
            cls.FONT_BODY = pygame.font.Font(None, 20)
            cls.FONT_SMALL = pygame.font.Font(None, 16)
            
            # Tentar carregar fontes customizadas se existirem
            fonts_dir = Path("assets/fonts")
            if (fonts_dir / "IMFellEnglishSC.ttf").exists():
                cls.FONT_TITLE = pygame.font.Font(str(fonts_dir / "IMFellEnglishSC.ttf"), 32)
            if (fonts_dir / "CormorantGaramond.ttf").exists():
                cls.FONT_BODY = pygame.font.Font(str(fonts_dir / "CormorantGaramond.ttf"), 20)
                
        except Exception:
            # Fallback para fontes padrão
            cls.FONT_TITLE = pygame.font.Font(None, 32)
            cls.FONT_SUBTITLE = pygame.font.Font(None, 24)
            cls.FONT_BODY = pygame.font.Font(None, 20)
            cls.FONT_SMALL = pygame.font.Font(None, 16)
    
    # === LAYOUT ===
    CARD_SIZE = (140, 200)
    CARD_GAP = 24
    CARD_HOVER_LIFT = 12
    CARD_HOVER_SCALE = 1.05
    
    # Zonas da tela (proporções)
    ZONE_ENEMY_HEIGHT = 0.25
    ZONE_HAND_HEIGHT = 0.20
    ZONE_STATUS_WIDTH = 260
    ZONE_STATUS_HEIGHT = 120
    
    # === ANIMAÇÃO ===
    ANIMATION_FPS = 30
    GLOW_SPEED = 0.015
    PARTICLE_LIFE = 0.4
    
    # === UTILIDADES ===
    @classmethod
    def get_color(cls, name: str) -> Tuple[int, int, int]:
        """Retorna uma cor pelo nome."""
        return cls.COLORS.get(name, (255, 255, 255))
    
    @classmethod
    def get_color_with_alpha(cls, name: str, alpha: int = 255) -> Tuple[int, int, int, int]:
        """Retorna uma cor com alpha."""
        color = cls.get_color(name)
        return (*color, alpha)
    
    @classmethod
    def scale_rect_to_screen(cls, base_rect: pygame.Rect, screen_size: Tuple[int, int]) -> pygame.Rect:
        """Escala um retângulo base para o tamanho da tela."""
        sw, sh = screen_size
        
        # Calcular proporções
        x_prop = base_rect.x / 1920.0
        y_prop = base_rect.y / 1080.0
        w_prop = base_rect.width / 1920.0
        h_prop = base_rect.height / 1080.0
        
        # Aplicar ao tamanho atual
        return pygame.Rect(
            int(x_prop * sw),
            int(y_prop * sh),
            int(w_prop * sw),
            int(h_prop * sh)
        )
    
    @classmethod
    def create_zones(cls, screen_size: Tuple[int, int]) -> Dict[str, pygame.Rect]:
        """Cria as zonas da interface baseadas no tamanho da tela."""
        sw, sh = screen_size
        
        return {
            "enemy": pygame.Rect(0, 0, sw, int(sh * cls.ZONE_ENEMY_HEIGHT)),
            "hand": pygame.Rect(0, int(sh * (1 - cls.ZONE_HAND_HEIGHT)), sw, int(sh * cls.ZONE_HAND_HEIGHT)),
            "status": pygame.Rect(sw - cls.ZONE_STATUS_WIDTH - 20, 20, cls.ZONE_STATUS_WIDTH, cls.ZONE_STATUS_HEIGHT),
            "player": pygame.Rect(int(sw * 0.1), int(sh * 0.4), int(sw * 0.3), int(sh * 0.4))
        }
    
    @classmethod
    def draw_text_outline(cls, surface: pygame.Surface, text: str, font: pygame.font.Font, 
                         pos: Tuple[int, int], color: Tuple[int, int, int], 
                         outline_color: Tuple[int, int, int] = (0, 0, 0), outline_width: int = 2):
        """Desenha texto com contorno."""
        x, y = pos
        
        # Desenhar contorno
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    outline_surf = font.render(text, True, outline_color)
                    surface.blit(outline_surf, (x + dx, y + dy))
        
        # Desenhar texto principal
        text_surf = font.render(text, True, color)
        surface.blit(text_surf, pos)
    
    @classmethod
    def draw_health_bar(cls, surface: pygame.Surface, rect: pygame.Rect, 
                       current: int, maximum: int, bar_type: str = "hp"):
        """Desenha uma barra de status (HP/Mana)."""
        # Cor baseada no tipo
        if bar_type == "hp":
            fill_color = cls.get_color("hp")
            bg_color = cls.get_color("hp_dark")
        elif bar_type == "mana":
            fill_color = cls.get_color("mana")
            bg_color = cls.get_color("mana_dark")
        else:
            fill_color = cls.get_color("silver")
            bg_color = (100, 100, 100)
        
        # Desenhar fundo
        pygame.draw.rect(surface, bg_color, rect)
        pygame.draw.rect(surface, (0, 0, 0), rect, 2)
        
        # Desenhar preenchimento
        if maximum > 0:
            fill_width = int((current / maximum) * (rect.width - 4))
            fill_rect = pygame.Rect(rect.x + 2, rect.y + 2, fill_width, rect.height - 4)
            pygame.draw.rect(surface, fill_color, fill_rect)
        
        # Texto
        text = f"{current}/{maximum}"
        text_surf = cls.FONT_SMALL.render(text, True, cls.get_color("text_light"))
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)
