"""
Medieval Deck - MVP Card View

Sistema de renderização de cartas para o MVP.
"""

import pygame
import math
import time
from typing import Tuple, Optional
from ..utils.theme import Theme
from ..gameplay.mvp_cards import Card

class CardView:
    """Visualização de uma carta no MVP."""
    
    def __init__(self, card: Card, position: Tuple[int, int]):
        self.card = card
        self.base_position = position
        self.current_position = list(position)
        self.hovered = False
        self.selected = False
        self.dragging = False
        
        # Estados de animação
        self.hover_offset = 0.0
        self.scale = 1.0
        self.glow_alpha = 0
        
        # Surface cache
        self._card_surface: Optional[pygame.Surface] = None
        self._needs_redraw = True
        
        # Tentar carregar frame da carta
        try:
            self.frame_image = pygame.image.load("assets/ui/card_frame.png").convert_alpha()
            # CORREÇÃO CRÍTICA: NÃO escalar automaticamente no carregamento
            # Deixar que o draw() faça a escala quando necessário
        except:
            # Criar frame placeholder
            self.frame_image = pygame.Surface(Theme.CARD_SIZE, pygame.SRCALPHA)
            self.frame_image.fill((139, 69, 19, 200))  # Marrom com transparência
            pygame.draw.rect(self.frame_image, (101, 67, 33), self.frame_image.get_rect(), 3)
    
    def update(self, dt: float):
        """Atualiza animações da carta."""
        target_lift = Theme.CARD_HOVER_LIFT if self.hovered else 0
        target_scale = Theme.CARD_HOVER_SCALE if self.hovered else 1.0
        
        # Animação suave
        self.hover_offset += (target_lift - self.hover_offset) * dt * 8
        self.scale += (target_scale - self.scale) * dt * 8
        
        # Glow pulsante quando selecionada
        if self.selected:
            self.glow_alpha = int(128 + 127 * math.sin(time.time() * Theme.GLOW_SPEED * 20))
        else:
            self.glow_alpha = 0
        
        # Atualizar posição
        self.current_position[1] = self.base_position[1] - self.hover_offset
        
        # Marcar para redesenho se houver mudanças significativas
        if abs(target_lift - self.hover_offset) > 0.1 or abs(target_scale - self.scale) > 0.01:
            self._needs_redraw = True
    
    def _create_card_surface(self) -> pygame.Surface:
        """Cria a surface da carta."""
        surface = pygame.Surface(Theme.CARD_SIZE, pygame.SRCALPHA)
        
        # Frame de fundo - escalar para Theme.CARD_SIZE
        if self.frame_image:
            scaled_frame = pygame.transform.smoothscale(self.frame_image, Theme.CARD_SIZE)
            surface.blit(scaled_frame, (0, 0))
        
        # Cor baseada no tipo de carta
        card_color = Theme.get_color(self.card.get_color())
        
        # Barra colorida do tipo
        type_rect = pygame.Rect(10, 10, Theme.CARD_SIZE[0] - 20, 8)
        pygame.draw.rect(surface, card_color, type_rect)
        
        # Custo de mana (canto superior direito)
        mana_circle = pygame.Rect(Theme.CARD_SIZE[0] - 35, 5, 30, 30)
        pygame.draw.ellipse(surface, Theme.get_color("mana"), mana_circle)
        pygame.draw.ellipse(surface, (0, 0, 0), mana_circle, 2)
        
        mana_text = Theme.FONT_SUBTITLE.render(str(self.card.mana_cost), True, Theme.get_color("text_light"))
        mana_rect = mana_text.get_rect(center=mana_circle.center)
        surface.blit(mana_text, mana_rect)
        
        # Nome da carta
        name_y = 45
        Theme.draw_text_outline(
            surface, self.card.name, Theme.FONT_TITLE,
            (10, name_y), Theme.get_color("text_light")
        )
        
        # Stats da carta
        stats_y = 80
        stats_text = []
        
        if self.card.damage > 0:
            stats_text.append(f"Damage: {self.card.damage}")
        if self.card.block > 0:
            stats_text.append(f"Block: {self.card.block}")
        if self.card.heal > 0:
            stats_text.append(f"Heal: {self.card.heal}")
        
        for i, stat in enumerate(stats_text):
            stat_surf = Theme.FONT_BODY.render(stat, True, card_color)
            surface.blit(stat_surf, (10, stats_y + i * 22))
        
        # Descrição
        desc_y = stats_y + len(stats_text) * 22 + 10
        desc_words = self.card.description.split()
        desc_lines = []
        current_line = ""
        
        for word in desc_words:
            test_line = f"{current_line} {word}".strip()
            test_surf = Theme.FONT_SMALL.render(test_line, True, Theme.get_color("text_dark"))
            if test_surf.get_width() > Theme.CARD_SIZE[0] - 20:
                if current_line:
                    desc_lines.append(current_line)
                    current_line = word
                else:
                    desc_lines.append(word)
                    current_line = ""
            else:
                current_line = test_line
        
        if current_line:
            desc_lines.append(current_line)
        
        for i, line in enumerate(desc_lines):
            line_surf = Theme.FONT_SMALL.render(line, True, Theme.get_color("text_dark"))
            surface.blit(line_surf, (10, desc_y + i * 18))
        
        return surface
    
    def draw(self, screen: pygame.Surface, pos=None, size=None, hover: bool = False):
        """Desenha a carta na tela com efeito de hover.
        
        Args:
            screen: Surface de destino
            pos: Posição da carta (x,y). Se None, usa current_position
            size: Tamanho da carta (w,h). Se None, usa tamanho padrão
            hover: Se a carta está em hover
        """
        if self._needs_redraw or self._card_surface is None:
            self._card_surface = self._create_card_surface()
            self._needs_redraw = False
        
        # Usar parâmetros ou valores padrão
        draw_pos = pos if pos is not None else self.current_position
        
        if size is not None:
            # CORREÇÃO CRÍTICA: Usar tamanho personalizado com escala correta
            w, h = size
            frame = pygame.transform.smoothscale(self._card_surface, size)
            card_rect = frame.get_rect()
            if isinstance(draw_pos, (list, tuple)) and len(draw_pos) == 2:
                card_rect.center = draw_pos
            else:
                card_rect.topleft = draw_pos
        else:
            # Calcular posição e escala padrão
            card_rect = self._card_surface.get_rect()
            card_rect.centerx = draw_pos[0]
            card_rect.bottom = draw_pos[1]
            frame = self._card_surface
        
        # Glow pulsante em hover
        if hover:
            glow = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
            alpha = int((math.sin(pygame.time.get_ticks() * 0.02) + 1) * 60)
            glow.fill((212, 180, 106, alpha))
            screen.blit(glow, card_rect.topleft, special_flags=pygame.BLEND_RGBA_ADD)
        
        # Glow de seleção
        if self.glow_alpha > 0:
            glow_surface = pygame.Surface((card_rect.width + 10, card_rect.height + 10), pygame.SRCALPHA)
            glow_surface.fill(Theme.get_color_with_alpha("glow_gold", self.glow_alpha))
            glow_rect = glow_surface.get_rect(center=card_rect.center)
            screen.blit(glow_surface, glow_rect, special_flags=pygame.BLEND_RGBA_ADD)
        
        # Aplicar escala se não estamos usando tamanho personalizado
        if size is None and abs(self.scale - 1.0) > 0.01:
            scaled_size = (int(card_rect.width * self.scale), int(card_rect.height * self.scale))
            scaled_surface = pygame.transform.scale(frame, scaled_size)
            scaled_rect = scaled_surface.get_rect(center=card_rect.center)
            screen.blit(scaled_surface, scaled_rect)
        else:
            screen.blit(frame, card_rect)
    
    def get_rect(self) -> pygame.Rect:
        """Retorna o retângulo da carta."""
        rect = pygame.Rect(0, 0, *Theme.CARD_SIZE)
        rect.centerx = self.current_position[0]
        rect.bottom = self.current_position[1]
        
        if abs(self.scale - 1.0) > 0.01:
            rect.width = int(rect.width * self.scale)
            rect.height = int(rect.height * self.scale)
            rect.centerx = self.current_position[0]
            rect.bottom = self.current_position[1]
        
        return rect
    
    def set_hovered(self, hovered: bool):
        """Define se a carta está sob hover."""
        if self.hovered != hovered:
            self.hovered = hovered
            self._needs_redraw = True
    
    def set_selected(self, selected: bool):
        """Define se a carta está selecionada."""
        if self.selected != selected:
            self.selected = selected
            self._needs_redraw = True
    
    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Verifica se um ponto está dentro da carta."""
        return self.get_rect().collidepoint(point)
