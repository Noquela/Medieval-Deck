"""
Sistema de UI clean com estética de pintura digital para Medieval Deck.

Implementa design cinematográfico com elementos pintados, efeitos atmosféricos
e animações suaves, utilizando assets IA carregados automaticamente.
"""

import pygame
import math
import random
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from ..utils.asset_loader import asset_loader, get_asset, get_button_states
from ..ui.animation import animate_to, EasingType
from ..ui.theme import theme

import logging
logger = logging.getLogger(__name__)


class ElementState(Enum):
    """Estados de elementos UI."""
    IDLE = "idle"
    HOVER = "hover" 
    PRESSED = "pressed"
    DISABLED = "disabled"


@dataclass
class PaintedElement:
    """
    Elemento UI com estética de pintura digital.
    
    Características:
    - Texturas IA para diferentes estados
    - Animações suaves com easing
    - Efeitos de pincel e glow atmosférico
    - Feedback visual responsivo
    """
    x: float
    y: float
    width: float
    height: float
    state: ElementState = ElementState.IDLE
    
    # Assets e texturas
    textures: Dict[str, pygame.Surface] = field(default_factory=dict)
    
    # Propriedades visuais
    scale: float = 1.0
    alpha: float = 255
    glow_intensity: float = 0.0
    brush_effect: float = 0.0
    
    # Animação
    target_scale: float = 1.0
    target_alpha: float = 255
    target_glow: float = 0.0
    
    # Callbacks
    on_click: Optional[Callable] = None
    on_hover: Optional[Callable] = None
    
    def __post_init__(self):
        """Inicialização pós-criação."""
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.animation_id = None


class PaintedButton(PaintedElement):
    """
    Botão com estética de pintura digital.
    
    Features:
    - Texturas metálicas geradas por IA
    - Estados visuais distintos (idle, hover, pressed)
    - Micro-animações e efeitos de glow
    - Texto integrado com tipografia medieval
    """
    
    def __init__(
        self,
        x: float, y: float, width: float, height: float,
        text: str,
        on_click: Optional[Callable] = None,
        style: str = "primary"
    ):
        super().__init__(x, y, width, height, on_click=on_click)
        self.text = text
        self.style = style
        
        # Carregar texturas dos botões
        self._load_button_textures()
        
        # Configuração visual
        self.text_color = theme.colors.PARCHMENT
        self.font = theme.typography.get_font('button')
        
        # Estados de hover/press
        self.is_hovered = False
        self.is_pressed = False
        
        logger.debug(f"PaintedButton criado: '{text}' em ({x}, {y})")
    
    def _load_button_textures(self):
        """Carrega texturas dos estados do botão."""
        button_states = get_button_states()
        
        # Redimensionar texturas para o tamanho do botão
        for state, surface in button_states.items():
            if surface:
                scaled_surface = pygame.transform.scale(surface, (int(self.width), int(self.height)))
                self.textures[state] = scaled_surface
        
        # Fallback se não tiver texturas
        if not self.textures:
            self._create_fallback_textures()
    
    def _create_fallback_textures(self):
        """Cria texturas fallback se não houver assets IA."""
        # Texturas procedurais simples
        for state in ['idle', 'hover', 'pressed']:
            surface = pygame.Surface((int(self.width), int(self.height)), pygame.SRCALPHA)
            
            if state == 'idle':
                color = (60, 45, 30, 200)  # Marrom metálico
            elif state == 'hover':
                color = (80, 60, 40, 220)  # Mais claro
            else:  # pressed
                color = (40, 30, 20, 180)  # Mais escuro
            
            pygame.draw.rect(surface, color, surface.get_rect(), border_radius=8)
            self.textures[state] = surface
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Processa eventos do botão.
        
        Args:
            event: Evento pygame
            
        Returns:
            True se evento foi processado
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.set_state(ElementState.PRESSED)
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_pressed:
                if self.rect.collidepoint(event.pos):
                    # Clique válido
                    if self.on_click:
                        self.on_click()
                    self.set_state(ElementState.HOVER if self.is_hovered else ElementState.IDLE)
                else:
                    self.set_state(ElementState.IDLE)
                return True
                
        elif event.type == pygame.MOUSEMOTION:
            was_hovered = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
            
            if self.is_hovered != was_hovered:
                if self.is_hovered:
                    self.set_state(ElementState.HOVER)
                    if self.on_hover:
                        self.on_hover()
                else:
                    self.set_state(ElementState.IDLE)
                return True
        
        return False
    
    def set_state(self, new_state: ElementState):
        """
        Altera estado do botão com animações.
        
        Args:
            new_state: Novo estado
        """
        if new_state == self.state:
            return
        
        old_state = self.state
        self.state = new_state
        
        # Atualizar flags
        self.is_pressed = (new_state == ElementState.PRESSED)
        
        # Animações baseadas no estado
        if new_state == ElementState.HOVER:
            self.target_scale = 1.05
            self.target_glow = 30
            animate_to(self, 'scale', 1.05, 0.2, EasingType.EASE_OUT)
            animate_to(self, 'glow_intensity', 30, 0.2, EasingType.EASE_OUT)
            
        elif new_state == ElementState.PRESSED:
            self.target_scale = 0.95
            self.target_glow = 50
            animate_to(self, 'scale', 0.95, 0.1, EasingType.EASE_IN)
            animate_to(self, 'glow_intensity', 50, 0.1, EasingType.EASE_IN)
            
        else:  # IDLE
            self.target_scale = 1.0
            self.target_glow = 0
            animate_to(self, 'scale', 1.0, 0.3, EasingType.EASE_OUT)
            animate_to(self, 'glow_intensity', 0, 0.3, EasingType.EASE_OUT)
    
    def update(self, dt: float):
        """
        Atualiza animações do botão.
        
        Args:
            dt: Delta time em segundos
        """
        # Atualizar rect com scale
        center = (self.x + self.width / 2, self.y + self.height / 2)
        scaled_width = self.width * self.scale
        scaled_height = self.height * self.scale
        
        self.rect = pygame.Rect(
            center[0] - scaled_width / 2,
            center[1] - scaled_height / 2,
            scaled_width,
            scaled_height
        )
    
    def draw(self, surface: pygame.Surface):
        """
        Desenha o botão com efeitos de pintura digital.
        
        Args:
            surface: Superfície de destino
        """
        # Selecionar textura baseada no estado
        texture_key = self.state.value
        if texture_key not in self.textures:
            texture_key = 'idle'
        
        texture = self.textures.get(texture_key)
        if not texture:
            return
        
        # Aplicar scale se necessário
        if abs(self.scale - 1.0) > 0.01:
            scaled_width = int(self.width * self.scale)
            scaled_height = int(self.height * self.scale)
            texture = pygame.transform.scale(texture, (scaled_width, scaled_height))
        
        # Posição centralizada
        center = (self.x + self.width / 2, self.y + self.height / 2)
        texture_rect = texture.get_rect(center=center)
        
        # Desenhar glow se presente
        if self.glow_intensity > 0:
            self._draw_glow(surface, texture_rect)
        
        # Desenhar textura
        if self.alpha < 255:
            texture = texture.copy()
            texture.set_alpha(int(self.alpha))
        
        surface.blit(texture, texture_rect)
        
        # Desenhar texto
        self._draw_text(surface, texture_rect)
    
    def _draw_glow(self, surface: pygame.Surface, rect: pygame.Rect):
        """
        Desenha efeito de glow atmosférico.
        
        Args:
            surface: Superfície de destino
            rect: Retângulo do botão
        """
        glow_color = (255, 215, 0)  # Dourado
        glow_radius = int(self.glow_intensity)
        
        if glow_radius <= 0:
            return
        
        # Criar surface de glow
        glow_size = (rect.width + glow_radius * 2, rect.height + glow_radius * 2)
        glow_surface = pygame.Surface(glow_size, pygame.SRCALPHA)
        
        # Desenhar múltiplos círculos para efeito difuso
        glow_center = (glow_size[0] // 2, glow_size[1] // 2)
        
        for i in range(glow_radius):
            alpha = int((glow_radius - i) * (self.glow_intensity / 100) * 2)
            alpha = min(alpha, 50)
            
            if alpha > 0:
                glow_color_alpha = (*glow_color, alpha)
                pygame.draw.ellipse(
                    glow_surface,
                    glow_color_alpha,
                    (glow_center[0] - rect.width//2 - i, 
                     glow_center[1] - rect.height//2 - i,
                     rect.width + i*2, 
                     rect.height + i*2)
                )
        
        # Posicionar glow
        glow_rect = glow_surface.get_rect(center=rect.center)
        surface.blit(glow_surface, glow_rect, special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def _draw_text(self, surface: pygame.Surface, button_rect: pygame.Rect):
        """
        Desenha texto do botão com tipografia medieval.
        
        Args:
            surface: Superfície de destino
            button_rect: Retângulo do botão
        """
        if not self.text:
            return
        
        # Renderizar texto
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)
        
        # Efeito de sombra
        shadow_color = (0, 0, 0, 100)
        shadow_surface = self.font.render(self.text, True, shadow_color)
        shadow_rect = shadow_surface.get_rect(center=(button_rect.centerx + 2, button_rect.centery + 2))
        
        surface.blit(shadow_surface, shadow_rect)
        surface.blit(text_surface, text_rect)


class ParallaxBackground:
    """
    Sistema de background com parallax e efeitos atmosféricos.
    
    Features:
    - Múltiplas camadas com movimento independente
    - Efeitos de blur e overlay
    - Movimento baseado na posição do mouse
    - Transições suaves entre cenários
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Camadas de parallax
        self.layers: List[Dict] = []
        self.current_background = None
        
        # Configuração de parallax
        self.mouse_x = screen_width // 2
        self.mouse_y = screen_height // 2
        self.parallax_strength = 20  # pixels de movimento máximo
        
        # Overlay atmosférico
        self.overlay_alpha = 0
        self.overlay_color = (0, 0, 0)
        
        logger.info("ParallaxBackground inicializado")
    
    def set_background(self, background_name: str, transition_time: float = 1.0):
        """
        Define um novo background com transição suave.
        
        Args:
            background_name: Nome do asset de background
            transition_time: Tempo de transição em segundos
        """
        background_surface = get_asset(background_name)
        
        if not background_surface:
            logger.warning(f"Background não encontrado: {background_name}")
            return
        
        # Redimensionar para tela
        scaled_bg = pygame.transform.scale(background_surface, (self.screen_width, self.screen_height))
        
        # Configurar camadas
        self.layers = [
            {
                'surface': scaled_bg,
                'depth': 1.0,  # Camada de fundo
                'offset_x': 0,
                'offset_y': 0,
                'alpha': 255
            }
        ]
        
        self.current_background = background_name
        
        # Aplicar blur sutil para atmosfera
        self._apply_atmospheric_effects()
        
        logger.info(f"Background definido: {background_name}")
    
    def _apply_atmospheric_effects(self):
        """Aplica efeitos atmosféricos ao background."""
        if not self.layers:
            return
        
        main_layer = self.layers[0]
        
        # Blur muito sutil
        # Note: pygame não tem blur nativo, implementar se necessário
        
        # Overlay escuro para destacar elementos frontais
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 40))  # 16% de opacidade
        
        self.layers.append({
            'surface': overlay,
            'depth': 0.8,
            'offset_x': 0,
            'offset_y': 0,
            'alpha': 255
        })
    
    def update_mouse_position(self, mouse_pos: Tuple[int, int]):
        """
        Atualiza posição do mouse para efeito parallax.
        
        Args:
            mouse_pos: Posição atual do mouse
        """
        self.mouse_x, self.mouse_y = mouse_pos
        
        # Calcular offsets de parallax
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        # Normalizar posição do mouse (-1 a 1)
        norm_x = (self.mouse_x - center_x) / center_x
        norm_y = (self.mouse_y - center_y) / center_y
        
        # Aplicar offsets às camadas baseado na profundidade
        for layer in self.layers:
            depth = layer['depth']
            layer['offset_x'] = norm_x * self.parallax_strength * depth
            layer['offset_y'] = norm_y * self.parallax_strength * depth * 0.5  # Menos movimento vertical
    
    def draw(self, surface: pygame.Surface):
        """
        Desenha todas as camadas de parallax.
        
        Args:
            surface: Superfície de destino
        """
        for layer in self.layers:
            layer_surface = layer['surface']
            offset_x = layer['offset_x']
            offset_y = layer['offset_y']
            alpha = layer['alpha']
            
            # Posição com offset de parallax
            x = offset_x
            y = offset_y
            
            # Aplicar alpha se necessário
            if alpha < 255:
                temp_surface = layer_surface.copy()
                temp_surface.set_alpha(alpha)
                surface.blit(temp_surface, (x, y))
            else:
                surface.blit(layer_surface, (x, y))


class AtmosphericParticles:
    """
    Sistema de partículas atmosféricas temáticas.
    
    Partículas específicas por personagem:
    - Knight: poeira dourada flutuante
    - Wizard: motas azuis cintilantes  
    - Assassin: névoa esverdeada
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles: List[Dict] = []
        self.theme = "neutral"
        
        # Configurações por tema
        self.theme_configs = {
            "knight": {
                "color": (255, 215, 0),  # Dourado
                "count": 30,
                "speed": (0.5, 1.5),
                "size": (2, 4),
                "twinkle": True
            },
            "wizard": {
                "color": (100, 150, 255),  # Azul mágico
                "count": 40,
                "speed": (0.3, 2.0),
                "size": (1, 3),
                "twinkle": True
            },
            "assassin": {
                "color": (50, 150, 80),  # Verde névoa
                "count": 25,
                "speed": (0.2, 1.0),
                "size": (3, 6),
                "twinkle": False
            },
            "neutral": {
                "color": (200, 200, 200),  # Cinza neutro
                "count": 20,
                "speed": (0.4, 1.2),
                "size": (2, 3),
                "twinkle": False
            }
        }
        
        logger.info("AtmosphericParticles inicializado")
    
    def set_theme(self, theme: str):
        """
        Define tema das partículas.
        
        Args:
            theme: Tema (knight, wizard, assassin, neutral)
        """
        if theme not in self.theme_configs:
            logger.warning(f"Tema de partículas desconhecido: {theme}")
            theme = "neutral"
        
        self.theme = theme
        self._generate_particles()
        
        logger.debug(f"Tema de partículas definido: {theme}")
    
    def _generate_particles(self):
        """Gera partículas baseadas no tema atual."""
        self.particles.clear()
        
        config = self.theme_configs[self.theme]
        
        for _ in range(config["count"]):
            particle = {
                'x': random.uniform(0, self.screen_width),
                'y': random.uniform(0, self.screen_height),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(*config["speed"]) * -1,  # Movimento para cima
                'size': random.uniform(*config["size"]),
                'color': config["color"],
                'alpha': random.uniform(100, 255),
                'twinkle_phase': random.uniform(0, math.pi * 2) if config["twinkle"] else 0,
                'life': 1.0
            }
            self.particles.append(particle)
    
    def update(self, dt: float):
        """
        Atualiza posições e estados das partículas.
        
        Args:
            dt: Delta time em segundos
        """
        config = self.theme_configs[self.theme]
        
        for particle in self.particles[:]:  # Cópia para modificação segura
            # Movimento
            particle['x'] += particle['vx'] * dt * 60
            particle['y'] += particle['vy'] * dt * 60
            
            # Twinkle effect
            if config["twinkle"]:
                particle['twinkle_phase'] += dt * 3
                twinkle_factor = (math.sin(particle['twinkle_phase']) + 1) / 2
                particle['alpha'] = 100 + twinkle_factor * 155
            
            # Reciclar partículas que saíram da tela
            if particle['y'] < -10:
                particle['y'] = self.screen_height + 10
                particle['x'] = random.uniform(0, self.screen_width)
            
            if particle['x'] < -10:
                particle['x'] = self.screen_width + 10
            elif particle['x'] > self.screen_width + 10:
                particle['x'] = -10
    
    def draw(self, surface: pygame.Surface):
        """
        Desenha todas as partículas.
        
        Args:
            surface: Superfície de destino
        """
        for particle in self.particles:
            # Criar surface temporária para alpha
            particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            
            color_with_alpha = (*particle['color'], int(particle['alpha']))
            pygame.draw.circle(
                particle_surface,
                color_with_alpha,
                (particle['size'], particle['size']),
                particle['size']
            )
            
            # Desenhar na tela
            surface.blit(
                particle_surface,
                (particle['x'] - particle['size'], particle['y'] - particle['size']),
                special_flags=pygame.BLEND_ALPHA_SDL2
            )


# Instâncias globais para uso fácil
painted_ui = None
parallax_bg = None
atmospheric_particles = None


def initialize_painted_ui(screen_width: int, screen_height: int):
    """
    Inicializa sistema de UI painted.
    
    Args:
        screen_width: Largura da tela
        screen_height: Altura da tela
    """
    global painted_ui, parallax_bg, atmospheric_particles
    
    # Carregar assets IA
    asset_loader.load_all_assets()
    
    # Inicializar sistemas
    parallax_bg = ParallaxBackground(screen_width, screen_height)
    atmospheric_particles = AtmosphericParticles(screen_width, screen_height)
    
    logger.info("Sistema Painted UI inicializado")


def create_painted_button(x: float, y: float, width: float, height: float, text: str, on_click: Callable = None) -> PaintedButton:
    """
    Cria um botão com estética painted.
    
    Args:
        x, y: Posição
        width, height: Dimensões
        text: Texto do botão
        on_click: Callback de clique
        
    Returns:
        PaintedButton configurado
    """
    return PaintedButton(x, y, width, height, text, on_click)
