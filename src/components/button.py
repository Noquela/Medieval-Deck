"""
Componente de botão medieval avançado com animações e estados.

Suporta texturas geradas por IA, múltiplos estados visuais,
animações de hover/click e efeitos de brilho.
"""

import pygame
import time
from typing import Optional, Callable, Tuple, Dict, Any
from enum import Enum

from ..ui.theme import theme, draw_text_with_shadow, create_gradient_surface, create_glow_surface
from ..ui.animation import animation_manager, EasingType


class ButtonState(Enum):
    """Estados visuais do botão."""
    NORMAL = "normal"
    HOVER = "hover" 
    PRESSED = "pressed"
    DISABLED = "disabled"


class Button:
    """
    Botão medieval cinematográfico com animações avançadas.
    
    Suporta:
    - Assets gerados por IA para texturas
    - Estados visuais (normal, hover, pressed, disabled)
    - Animações suaves de hover e click
    - Efeitos de brilho e sombra
    - Feedback visual e sonoro
    """
    
    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 text: str = "",
                 font_type: str = "button",
                 on_click: Optional[Callable] = None,
                 style: str = "default"):
        """
        Inicializa botão medieval.
        
        Args:
            x, y: Posição
            width, height: Dimensões
            text: Texto do botão
            font_type: Tipo de fonte (ver theme.py)
            on_click: Callback de clique
            style: Estilo visual ("default", "primary", "secondary")
        """
        # Posição e dimensões
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        
        # Propriedades visuais
        self.text = text
        self.font = theme.typography.get_font(font_type)
        self.style = style
        
        # Estado e interação
        self.state = ButtonState.NORMAL
        self.is_enabled = True
        self.on_click = on_click
        
        # Propriedades animáveis
        self.scale = 1.0
        self.alpha = 255
        self.glow_intensity = 0.0
        self.shadow_offset = theme.spacing.SHADOW_OFFSET_MEDIUM
        
        # Texturas e superfícies
        self.textures: Dict[str, pygame.Surface] = {}
        self.glow_surface: Optional[pygame.Surface] = None
        
        # Estado interno
        self._last_mouse_pos = (0, 0)
        self._is_mouse_down = False
        self._glow_timer = 0.0
        
        # Inicializa assets
        self._create_default_textures()
        self._create_glow_surface()
    
    def _create_default_textures(self):
        """Cria texturas padrão caso não tenham sido geradas por IA."""
        colors = self._get_style_colors()
        
        for state in ButtonState:
            state_name = state.value
            
            if state == ButtonState.NORMAL:
                color = colors['primary']
            elif state == ButtonState.HOVER:
                color = colors['hover']
            elif state == ButtonState.PRESSED:
                color = colors['pressed']
            else:  # DISABLED
                color = colors['disabled']
            
            # Cria superfície com gradiente
            surface = create_gradient_surface(
                (self.width, self.height),
                color,
                tuple(max(0, c - 30) for c in color)  # Tom mais escuro embaixo
            )
            
            # Adiciona borda chamfered
            self._add_bevel_effect(surface, state)
            
            self.textures[state_name] = surface
    
    def _get_style_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Retorna cores baseadas no estilo do botão."""
        if self.style == "primary":
            return {
                'primary': theme.colors.GOLD_PRIMARY,
                'hover': theme.colors.GOLD_LIGHT,
                'pressed': theme.colors.GOLD_DARK,
                'disabled': theme.colors.STONE_MEDIUM
            }
        elif self.style == "secondary":
            return {
                'primary': theme.colors.STONE_MEDIUM,
                'hover': theme.colors.STONE_LIGHT,
                'pressed': theme.colors.STONE_DARK,
                'disabled': theme.colors.STONE_DARK
            }
        else:  # default
            return {
                'primary': theme.colors.PURPLE_MYSTICAL,
                'hover': theme.colors.PURPLE_LIGHT,
                'pressed': (50, 0, 100),  # Púrpura mais escuro
                'disabled': theme.colors.STONE_MEDIUM
            }
    
    def _add_bevel_effect(self, surface: pygame.Surface, state: ButtonState):
        """Adiciona efeito de chanfro 3D."""
        rect = surface.get_rect()
        
        # Cores do chanfro
        if state == ButtonState.PRESSED:
            highlight_color = theme.colors.STONE_DARK
            shadow_color = theme.colors.GOLD_LIGHT
        else:
            highlight_color = theme.colors.GOLD_LIGHT
            shadow_color = theme.colors.STONE_DARK
        
        # Linhas de highlight (topo e esquerda)
        pygame.draw.line(surface, highlight_color, (0, 0), (rect.width - 1, 0), 2)
        pygame.draw.line(surface, highlight_color, (0, 0), (0, rect.height - 1), 2)
        
        # Linhas de sombra (baixo e direita)
        pygame.draw.line(surface, shadow_color, (rect.width - 1, 0), (rect.width - 1, rect.height - 1), 2)
        pygame.draw.line(surface, shadow_color, (0, rect.height - 1), (rect.width - 1, rect.height - 1), 2)
    
    def _create_glow_surface(self):
        """Cria superfície de brilho para efeitos de hover."""
        if theme.enable_glow_effects:
            glow_size = (self.width + 20, self.height + 20)
            self.glow_surface = create_glow_surface(
                glow_size,
                theme.colors.GOLD_LIGHT,
                intensity=0.4
            )
    
    def set_texture(self, state: ButtonState, texture: pygame.Surface):
        """Define textura personalizada para um estado."""
        self.textures[state.value] = texture
    
    def load_ai_textures(self, texture_paths: Dict[str, str]):
        """
        Carrega texturas geradas por IA.
        
        Args:
            texture_paths: Dicionário {estado: caminho_arquivo}
        """
        for state_name, path in texture_paths.items():
            try:
                texture = pygame.image.load(path).convert_alpha()
                texture = pygame.transform.scale(texture, (self.width, self.height))
                self.textures[state_name] = texture
            except Exception as e:
                print(f"Erro ao carregar textura {path}: {e}")
    
    def update(self, dt: float):
        """
        Atualiza animações e estado do botão.
        
        Args:
            dt: Delta time em segundos
        """
        # Atualiza timer de brilho
        if self.state == ButtonState.HOVER and theme.enable_glow_effects:
            self._glow_timer += dt * 3.0  # Velocidade da pulsação
            self.glow_intensity = 0.3 + 0.2 * abs(pygame.math.Vector2(1, 0).rotate(self._glow_timer * 180).x)
        else:
            self.glow_intensity = 0.0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Processa eventos de input.
        
        Args:
            event: Evento do pygame
            
        Returns:
            True se o evento foi consumido
        """
        if not self.is_enabled:
            return False
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_over = self.rect.collidepoint(mouse_pos)
        
        if event.type == pygame.MOUSEMOTION:
            self._last_mouse_pos = mouse_pos
            
            # Detecta hover
            if mouse_over and self.state == ButtonState.NORMAL:
                self._on_hover_start()
            elif not mouse_over and self.state == ButtonState.HOVER:
                self._on_hover_end()
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and mouse_over:  # Botão esquerdo
                self._on_press_start()
                self._is_mouse_down = True
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self._is_mouse_down:  # Botão esquerdo
                self._is_mouse_down = False
                self._on_press_end()
                
                # Executa callback se ainda sobre o botão
                if mouse_over and self.on_click:
                    self.on_click()
                return True
        
        return False
    
    def _on_hover_start(self):
        """Inicia estado de hover."""
        self.state = ButtonState.HOVER
        
        # Animação de escala
        animation_manager.animate(
            target=self,
            property_name='scale',
            end_value=1.05,
            duration=0.1,
            easing=EasingType.EASE_OUT
        )
        
        # Animação de sombra
        animation_manager.animate(
            target=self,
            property_name='shadow_offset',
            end_value=theme.spacing.SHADOW_OFFSET_LARGE,
            duration=0.1,
            easing=EasingType.EASE_OUT
        )
    
    def _on_hover_end(self):
        """Termina estado de hover."""
        if self.state == ButtonState.HOVER:
            self.state = ButtonState.NORMAL
            
            # Retorna ao tamanho normal
            animation_manager.animate(
                target=self,
                property_name='scale',
                end_value=1.0,
                duration=0.1,
                easing=EasingType.EASE_OUT
            )
            
            # Retorna sombra normal
            animation_manager.animate(
                target=self,
                property_name='shadow_offset',
                end_value=theme.spacing.SHADOW_OFFSET_MEDIUM,
                duration=0.1,
                easing=EasingType.EASE_OUT
            )
    
    def _on_press_start(self):
        """Inicia estado de pressionado."""
        self.state = ButtonState.PRESSED
        
        # Animação de "pressionar"
        animation_manager.animate(
            target=self,
            property_name='scale',
            end_value=0.95,
            duration=0.05,
            easing=EasingType.EASE_IN
        )
    
    def _on_press_end(self):
        """Termina estado de pressionado."""
        # Verifica se ainda está com hover
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            self.state = ButtonState.HOVER
            scale_target = 1.05
        else:
            self.state = ButtonState.NORMAL
            scale_target = 1.0
        
        # Animação de retorno
        animation_manager.animate(
            target=self,
            property_name='scale',
            end_value=scale_target,
            duration=0.1,
            easing=EasingType.EASE_OUT
        )
    
    def set_enabled(self, enabled: bool):
        """Habilita/desabilita botão."""
        self.is_enabled = enabled
        self.state = ButtonState.NORMAL if enabled else ButtonState.DISABLED
        
        # Animação de fade
        target_alpha = 255 if enabled else 128
        animation_manager.animate(
            target=self,
            property_name='alpha',
            end_value=target_alpha,
            duration=0.2,
            easing=EasingType.EASE_OUT
        )
    
    def draw(self, surface: pygame.Surface):
        """
        Desenha botão na superfície.
        
        Args:
            surface: Superfície de destino
        """
        # Calcula posição e tamanho com escala
        scaled_width = int(self.width * self.scale)
        scaled_height = int(self.height * self.scale)
        scaled_x = self.x + (self.width - scaled_width) // 2
        scaled_y = self.y + (self.height - scaled_height) // 2
        
        # Desenha brilho de fundo (se hover)
        if (self.glow_surface and self.glow_intensity > 0 and 
            theme.enable_glow_effects):
            glow_alpha = int(255 * self.glow_intensity)
            glow_surf = self.glow_surface.copy()
            glow_surf.set_alpha(glow_alpha)
            
            glow_x = scaled_x - 10
            glow_y = scaled_y - 10
            surface.blit(glow_surf, (glow_x, glow_y))
        
        # Desenha sombra
        if theme.enable_shadows and self.shadow_offset > 0:
            shadow_surface = pygame.Surface((scaled_width, scaled_height))
            shadow_surface.fill(theme.colors.SHADOW_BLACK)
            shadow_surface.set_alpha(128)
            
            shadow_x = scaled_x + self.shadow_offset
            shadow_y = scaled_y + self.shadow_offset
            surface.blit(shadow_surface, (shadow_x, shadow_y))
        
        # Desenha textura do botão
        texture_key = self.state.value
        if texture_key in self.textures:
            texture = self.textures[texture_key]
            
            # Escala textura se necessário
            if self.scale != 1.0:
                texture = pygame.transform.scale(
                    texture, 
                    (scaled_width, scaled_height)
                )
            
            # Aplica transparência
            if self.alpha < 255:
                texture = texture.copy()
                texture.set_alpha(self.alpha)
            
            surface.blit(texture, (scaled_x, scaled_y))
        
        # Desenha texto
        if self.text:
            self._draw_text(surface, scaled_x, scaled_y, scaled_width, scaled_height)
    
    def _draw_text(self, surface: pygame.Surface, x: int, y: int, width: int, height: int):
        """Desenha texto centralizado no botão."""
        # Cor do texto baseada no estado
        if self.state == ButtonState.DISABLED:
            text_color = theme.colors.STONE_DARK
        elif self.state == ButtonState.PRESSED:
            text_color = theme.colors.PARCHMENT
        else:
            text_color = theme.colors.PARCHMENT
        
        # Renderiza texto
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect()
        
        # Centraliza
        text_x = x + (width - text_rect.width) // 2
        text_y = y + (height - text_rect.height) // 2
        
        # Ajuste de posição para efeito de pressionar
        if self.state == ButtonState.PRESSED:
            text_y += 1
        
        # Desenha com sombra
        if theme.enable_shadows:
            shadow_color = theme.colors.SHADOW_BLACK
            draw_text_with_shadow(
                surface, self.text, self.font,
                (text_x, text_y), text_color, shadow_color, (1, 1)
            )
        else:
            surface.blit(text_surface, (text_x, text_y))


class IconButton(Button):
    """Botão apenas com ícone (para setas de navegação)."""
    
    def __init__(self,
                 x: int,
                 y: int,
                 size: int,
                 icon_surface: pygame.Surface,
                 on_click: Optional[Callable] = None):
        """
        Inicializa botão de ícone.
        
        Args:
            x, y: Posição
            size: Tamanho (quadrado)
            icon_surface: Superfície do ícone
            on_click: Callback de clique
        """
        super().__init__(x, y, size, size, "", "label", on_click, "secondary")
        self.icon = icon_surface
        self.icon_size = size - theme.spacing.PADDING_MEDIUM
    
    def _draw_text(self, surface: pygame.Surface, x: int, y: int, width: int, height: int):
        """Sobrescreve para desenhar ícone em vez de texto."""
        if self.icon:
            # Escala ícone
            icon_surface = pygame.transform.scale(
                self.icon,
                (self.icon_size, self.icon_size)
            )
            
            # Aplica cor baseada no estado
            if self.state == ButtonState.DISABLED:
                icon_surface = icon_surface.copy()
                icon_surface.fill(theme.colors.STONE_DARK, special_flags=pygame.BLEND_MULT)
            
            # Centraliza ícone
            icon_x = x + (width - self.icon_size) // 2
            icon_y = y + (height - self.icon_size) // 2
            
            # Ajuste para efeito de pressionar
            if self.state == ButtonState.PRESSED:
                icon_y += 1
            
            surface.blit(icon_surface, (icon_x, icon_y))
