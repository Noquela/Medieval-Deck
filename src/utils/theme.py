"""
Medieval Deck - Theme Configuration

Centraliza cores, fontes e constantes visuais para o MVP com assets IA.
"""

import pygame
import math
from pathlib import Path    @classmethod
    def draw_text_outline(cls, surface: pygame.Surface, text: str, font: pygame.font.Font, 
                         pos: Tuple[int, int], color: Tuple[int, int, int], 
                         outline_color: Tuple[int, int, int] = (0, 0, 0), outline_width: int = 1):
        """Desenha texto com contorno."""
        x, y = pos
        
        # Contorno
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    outline_surf = font.render(text, True, outline_color)
                    surface.blit(outline_surf, (x + dx, y + dy))
        
        # Texto principal
        text_surf = font.render(text, True, color)
        surface.blit(text_surf, pos)
    
    @classmethod
    def get_color_with_alpha(cls, color_name: str, alpha: int) -> Tuple[int, int, int, int]:
        """
        Retorna uma cor do tema com alpha específico.
        
        Args:
            color_name: Nome da cor no tema
            alpha: Valor alpha (0-255)
            
        Returns:
            Tupla RGBA
        """
        color = cls.COLORS.get(color_name, cls.COLORS["text_light"])
        return (*color, alpha)
    
    @classmethod
    def calculate_glow_alpha(cls, time_ms: int) -> int:
        """
        Calcula o alpha do glow pulsante baseado no tempo.
        
        Args:
            time_ms: Tempo atual em millisegundos
            
        Returns:
            Valor alpha para o glow
        """
        progress = (time_ms % cls.TIMINGS["hover_glow_period"]) / cls.TIMINGS["hover_glow_period"]
        sine_wave = math.sin(progress * 2 * math.pi)
        alpha_range = cls.GLOW["alpha_max"] - cls.GLOW["alpha_min"]
        return cls.GLOW["alpha_min"] + int((sine_wave + 1) * 0.5 * alpha_range)
    
    @classmethod
    def load_sprite_sheet(cls, path: str, frame_count: int) -> list:
        """
        Carrega uma sprite sheet e divide em frames.
        
        Args:
            path: Caminho para a sprite sheet
            frame_count: Número de frames na sheet
            
        Returns:
            Lista de surfaces dos frames
        """
        try:
            sheet = pygame.image.load(path).convert_alpha()
            frame_width = sheet.get_width() // frame_count
            frame_height = sheet.get_height()
            
            frames = []
            for i in range(frame_count):
                frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                frame = sheet.subsurface(frame_rect).copy()
                frames.append(frame)
            
            return frames
        except Exception as e:
            print(f"Error loading sprite sheet {path}: {e}")
            # Return empty frames
            return [pygame.Surface((64, 64), pygame.SRCALPHA) for _ in range(frame_count)]rt Dict, Tuple

class Theme:
    """Configuração visual centralizada do Medieval Deck."""
    
    # === CORES EXPANDIDAS ===
    COLORS = {
        # Principais
        "gold": (212, 180, 106),          # Dourado medieval
        "dark_gold": (160, 140, 80),      # Dourado escuro
        "light_gold": (240, 220, 160),    # Dourado claro
        "gold_dark": (180, 150, 80),      # Compatibilidade
        "silver": (192, 192, 192),
        
        # Health and mana
        "hp": (224, 68, 58),              # Vermelho HP
        "hp_red": (224, 68, 58),          # Alias
        "hp_dark": (180, 40, 30),         # HP escuro
        "mana": (39, 131, 221),           # Azul mana
        "mana_blue": (39, 131, 221),      # Alias
        "mana_dark": (25, 80, 140),       # Mana escuro
        "block": (100, 150, 255),         # Azul do bloqueio
        "block_blue": (100, 150, 255),    # Alias
        
        # UI elements
        "ui_mask": (18, 11, 5, 140),      # Máscara semi-transparente
        "background": (25, 20, 15),       # Fundo escuro
        "border": (100, 80, 60),          # Bordas
        "text_light": (245, 240, 230),    # Texto claro
        "text_dark": (40, 30, 20),        # Texto escuro
        
        # Card states
        "card_bg": (60, 50, 40),          # Fundo carta normal
        "card_selected": (120, 100, 70),  # Carta selecionada
        "card_hover": (100, 85, 60),      # Carta em hover
        "selected": (120, 100, 70),       # Alias para compatibilidade
        
        # Card types
        "card_attack": (220, 68, 58),
        "card_defense": (150, 150, 150),
        "card_magic": (39, 131, 221),
        "card_heal": (68, 220, 68),
        
        # Effects and particles
        "glow_gold": (255, 215, 0, 128),
        "particles_hit": (255, 100, 100),
        "particles_heal": (100, 255, 100),
        "particles_magic": (100, 100, 255),
        "particle_gold": (255, 215, 0),   # Partículas douradas
        "particle_red": (255, 100, 100),  # Partículas de dano
        "particle_blue": (100, 150, 255), # Partículas de bloqueio
        "heal_green": (100, 255, 100),    # Verde da cura
        "damage_red": (255, 100, 100),    # Vermelho do dano
    }
    
    # === LAYOUT CONSTANTS ===
    LAYOUT = {
        "card_aspect": 0.67,              # Proporção altura/largura das cartas
        "hand_bottom_margin": 0.15,       # Margem inferior da mão (% da tela)
        "enemy_ground_line": 0.55,        # Linha do chão para inimigos (% da tela)
        "player_ground_line": 0.55,       # Linha do chão para jogador (% da tela)
        "card_hover_lift": 12,            # Pixels que a carta levanta no hover
        "card_hover_scale": 1.05,         # Escala da carta no hover
        "torch_flicker_speed": 6,         # FPS da animação da tocha
    }
    
    # === ANIMATION TIMINGS ===
    TIMINGS = {
        "card_play_duration": 300,        # Duração da animação de jogar carta
        "attack_duration": 500,           # Duração da animação de ataque
        "floating_number_duration": 1200, # Duração dos números flutuantes
        "particle_duration": 800,         # Duração dos efeitos de partícula
        "camera_shake_frames": 4,         # Frames de camera shake
        "hover_glow_period": 2000,        # Período do glow pulsante (ms)
    }
    
    # === GLOW EFFECT SETTINGS ===
    GLOW = {
        "alpha_min": 40,                  # Alpha mínimo do glow
        "alpha_max": 120,                 # Alpha máximo do glow
        "size_offset": 10,                # Pixels extras para o glow
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
