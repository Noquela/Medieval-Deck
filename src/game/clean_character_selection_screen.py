"""
Tela de seleção de personagem redesenhada com estética clean e pintura digital.

Features:
- Carrossel de backgrounds que muda com setas laterais
- Sprites transparentes sem moldura com glow atmosférico
- Painel de informações semi-transparente
- Barras de atributos estilizadas com animações
- Partículas temáticas por personagem
- Parallax baseado na posição do mouse
"""

import pygame
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from ..ui.painted_ui import (
    initialize_painted_ui,
    create_painted_button,
    parallax_bg,
    atmospheric_particles,
    PaintedButton
)
from ..ui.animation import animate_to, EasingType, animation_manager
from ..ui.theme import theme
from ..utils.asset_loader import get_asset, get_character_assets

logger = logging.getLogger(__name__)


@dataclass
class CharacterData:
    """Dados de um personagem para exibição clean."""
    id: str
    name: str
    subtitle: str
    description: str
    attributes: Dict[str, int]
    color_theme: Tuple[int, int, int]
    particle_theme: str


class CleanCharacterSelectionScreen:
    """
    Tela de seleção de personagem com design clean e pintura digital.
    
    Layout:
    - Background: carrossel de cenários vazios (sem personagem)
    - Sprite: PNG transparente posicionado à esquerda com glow
    - Painel Info: semi-transparente sobre o fundo
    - Setas: ícones ornamentais para navegação
    - Barras: atributos com cores temáticas e animações
    """
    
    def __init__(self, screen: pygame.Surface, config, asset_generator=None):
        self.screen = screen
        self.config = config
        self.asset_generator = asset_generator
        
        # Dimensões da tela
        self.screen_width = config.ui.window_width
        self.screen_height = config.ui.window_height
        
        # Estado da seleção
        self.current_character_index = 0
        self.characters = []
        self.initialized = False
        self.intro_complete = False
        self.pending_action = None
        
        # Elementos UI
        self.navigation_buttons: Dict[str, PaintedButton] = {}
        self.action_buttons: Dict[str, PaintedButton] = {}
        
        # Animações
        self.sprite_alpha = 0
        self.panel_alpha = 0
        self.attributes_alpha = 0
        
        # Layout
        self.sprite_rect = None
        self.panel_rect = None
        
        # Inicializar
        self._setup_characters()
        self._initialize_ui()
        self._create_buttons()
        
        logger.info("CleanCharacterSelectionScreen inicializado")
    
    def _setup_characters(self):
        """Configura dados dos personagens."""
        self.characters = [
            CharacterData(
                id="knight",
                name="Cavaleiro Valente",
                subtitle="Defensor do Reino",
                description="Um nobre guerreiro dedicado à proteção dos inocentes. Sua força e honra são lendárias nas terras medievais, empunhando sua espada com maestria incomparável.",
                attributes={"Vida": 35, "Ataque": 25, "Defesa": 30, "Magia": 10},
                color_theme=(255, 215, 0),  # Dourado
                particle_theme="knight"
            ),
            CharacterData(
                id="wizard",
                name="Mestre Arcano",
                subtitle="Guardião dos Mistérios",
                description="Estudioso das artes místicas, capaz de manipular as forças elementais. Seus conhecimentos antigos são a chave para desvendar os segredos do reino.",
                attributes={"Vida": 20, "Ataque": 35, "Defesa": 15, "Magia": 30},
                color_theme=(100, 150, 255),  # Azul mágico
                particle_theme="wizard"
            ),
            CharacterData(
                id="assassin",
                name="Assassino das Sombras",
                subtitle="Lâmina Silenciosa",
                description="Mestre da furtividade e precisão mortal. Move-se nas sombras como fantasma, eliminando ameaças antes que percebam sua presença.",
                attributes={"Vida": 25, "Ataque": 30, "Defesa": 20, "Magia": 25},
                color_theme=(50, 150, 80),  # Verde névoa
                particle_theme="assassin"
            )
        ]
    
    def _initialize_ui(self):
        """Inicializa sistema de UI painted."""
        if not self.initialized:
            initialize_painted_ui(self.screen_width, self.screen_height)
            self.initialized = True
            
        # Configurar layout
        self._setup_layout()
        
        # Carregar primeiro personagem
        self._load_character(0)
    
    def _setup_layout(self):
        """Define áreas de layout da tela."""
        # Área do sprite (lado esquerdo)
        sprite_width = 400
        sprite_height = 600
        sprite_x = self.screen_width * 0.15
        sprite_y = (self.screen_height - sprite_height) // 2
        
        self.sprite_rect = pygame.Rect(sprite_x, sprite_y, sprite_width, sprite_height)
        
        # Área do painel de informações (lado direito)
        panel_width = self.screen_width * 0.4
        panel_height = self.screen_height * 0.6
        panel_x = self.screen_width * 0.55
        panel_y = (self.screen_height - panel_height) // 2
        
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
    
    def _create_buttons(self):
        """Cria botões de navegação e ação."""
        # Setas de navegação
        arrow_size = 60
        arrow_y = self.screen_height // 2 - arrow_size // 2
        
        # Seta esquerda
        left_arrow = create_painted_button(
            50, arrow_y, arrow_size, arrow_size,
            "◀", lambda: self._trigger_action("previous")
        )
        self.navigation_buttons["left"] = left_arrow
        
        # Seta direita  
        right_arrow = create_painted_button(
            self.screen_width - 50 - arrow_size, arrow_y, arrow_size, arrow_size,
            "▶", lambda: self._trigger_action("next")
        )
        self.navigation_buttons["right"] = right_arrow
        
        # Botões de ação (rodapé)
        button_width = 200
        button_height = 60
        button_y = self.screen_height - 100
        
        # Botão Voltar
        back_button = create_painted_button(
            self.screen_width * 0.3 - button_width // 2, button_y,
            button_width, button_height,
            "VOLTAR", lambda: self._trigger_action("back_to_menu")
        )
        self.action_buttons["back"] = back_button
        
        # Botão Selecionar
        select_button = create_painted_button(
            self.screen_width * 0.7 - button_width // 2, button_y,
            button_width, button_height,
            "SELECIONAR", lambda: self._trigger_action("select_character")
        )
        self.action_buttons["select"] = select_button
        
        # Configurar alpha inicial
        for button in {**self.navigation_buttons, **self.action_buttons}.values():
            button.alpha = 0
    
    def _load_character(self, index: int):
        """
        Carrega assets e configura personagem atual.
        
        Args:
            index: Índice do personagem
        """
        if index < 0 or index >= len(self.characters):
            return
        
        character = self.characters[index]
        
        # Carregar background
        if parallax_bg:
            parallax_bg.set_background(f"{character.id}_bg")
        
        # Configurar partículas temáticas
        if atmospheric_particles:
            atmospheric_particles.set_theme(character.particle_theme)
        
        logger.info(f"Personagem carregado: {character.name}")
    
    def _trigger_action(self, action: str):
        """Armazena ação para ser processada."""
        if action == "previous":
            self._previous_character()
        elif action == "next":
            self._next_character()
        else:
            self.pending_action = action
    
    def _previous_character(self):
        """Muda para personagem anterior."""
        old_index = self.current_character_index
        self.current_character_index = (self.current_character_index - 1) % len(self.characters)
        
        if old_index != self.current_character_index:
            self._transition_character()
    
    def _next_character(self):
        """Muda para próximo personagem."""
        old_index = self.current_character_index
        self.current_character_index = (self.current_character_index + 1) % len(self.characters)
        
        if old_index != self.current_character_index:
            self._transition_character()
    
    def _transition_character(self):
        """Executa transição suave entre personagens."""
        # Fade out elementos
        animate_to(self, 'sprite_alpha', 0, 0.2, EasingType.EASE_IN)
        animate_to(self, 'panel_alpha', 0, 0.2, EasingType.EASE_IN)
        
        # Carregar novo personagem após fade out
        def load_new_character():
            self._load_character(self.current_character_index)
            # Fade in
            animate_to(self, 'sprite_alpha', 255, 0.3, EasingType.EASE_OUT)
            animate_to(self, 'panel_alpha', 255, 0.3, EasingType.EASE_OUT)
        
        # Agendar carregamento
        animate_to(self, 'attributes_alpha', 0, 0.1, EasingType.LINEAR, delay=0.2, on_complete=load_new_character)
    
    def enter_screen(self):
        """Chamado quando a tela é exibida."""
        if not self.intro_complete:
            self.start_intro_animations()
    
    def start_intro_animations(self):
        """Inicia animações de introdução sequencial."""
        # Sprite aparece primeiro
        animate_to(self, 'sprite_alpha', 255, 0.6, EasingType.EASE_OUT, delay=0.2)
        
        # Painel de informações
        animate_to(self, 'panel_alpha', 255, 0.5, EasingType.EASE_OUT, delay=0.5)
        
        # Atributos
        animate_to(self, 'attributes_alpha', 255, 0.4, EasingType.EASE_OUT, delay=0.8)
        
        # Botões com stagger
        buttons = list({**self.navigation_buttons, **self.action_buttons}.values())
        for i, button in enumerate(buttons):
            delay = 1.0 + i * 0.1
            animate_to(button, 'alpha', 255, 0.3, EasingType.EASE_OUT, delay=delay)
        
        # Marcar intro completo
        def mark_complete():
            self.intro_complete = True
        
        total_time = 1.0 + len(buttons) * 0.1 + 0.3
        animate_to(self, 'attributes_alpha', 255, 0.1, EasingType.LINEAR, delay=total_time, on_complete=mark_complete)
        
        logger.info("Animações de intro da seleção iniciadas")
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Processa eventos da tela de seleção.
        
        Args:
            event: Evento pygame
            
        Returns:
            Ação a ser executada ou None
        """
        # Atualizar posição do mouse para parallax
        if event.type == pygame.MOUSEMOTION:
            if parallax_bg:
                parallax_bg.update_mouse_position(event.pos)
        
        # Processar eventos dos botões
        all_buttons = {**self.navigation_buttons, **self.action_buttons}
        for button in all_buttons.values():
            if button.handle_event(event):
                # Verificar ação pendente
                if self.pending_action:
                    action = self.pending_action
                    self.pending_action = None
                    return action
                return None
        
        # Teclas de atalho
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self._previous_character()
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self._next_character()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return f"select_{self.characters[self.current_character_index].id}"
            elif event.key == pygame.K_ESCAPE:
                return "back_to_menu"
        
        return None
    
    def update(self, dt: float):
        """
        Atualiza animações e estado da tela.
        
        Args:
            dt: Delta time em segundos
        """
        # Atualizar animações globais
        animation_manager.update()
        
        # Atualizar partículas
        if atmospheric_particles:
            atmospheric_particles.update(dt)
        
        # Atualizar botões
        all_buttons = {**self.navigation_buttons, **self.action_buttons}
        for button in all_buttons.values():
            button.update(dt)
    
    def draw(self):
        """Desenha a tela de seleção completa."""
        # Limpar tela
        self.screen.fill((10, 10, 15))
        
        # Desenhar background com parallax
        if parallax_bg:
            parallax_bg.draw(self.screen)
        
        # Desenhar partículas atmosféricas
        if atmospheric_particles:
            atmospheric_particles.draw(self.screen)
        
        # Desenhar sprite do personagem
        self._draw_character_sprite()
        
        # Desenhar painel de informações
        self._draw_info_panel()
        
        # Desenhar botões
        all_buttons = {**self.navigation_buttons, **self.action_buttons}
        for button in all_buttons.values():
            if button.alpha > 0:
                button.draw(self.screen)
    
    def _draw_character_sprite(self):
        """Desenha sprite do personagem com glow atmosférico."""
        if self.sprite_alpha <= 0:
            return
        
        character = self.characters[self.current_character_index]
        
        # Carregar sprite
        sprite_surface = get_asset(f"{character.id}_sprite")
        if not sprite_surface:
            return
        
        # Redimensionar sprite para a área
        sprite_scaled = pygame.transform.scale(sprite_surface, (self.sprite_rect.width, self.sprite_rect.height))
        
        # Aplicar alpha
        if self.sprite_alpha < 255:
            sprite_scaled = sprite_scaled.copy()
            sprite_scaled.set_alpha(int(self.sprite_alpha))
        
        # Desenhar glow atmosférico
        self._draw_character_glow(character.color_theme)
        
        # Desenhar sprite
        self.screen.blit(sprite_scaled, self.sprite_rect)
    
    def _draw_character_glow(self, color: Tuple[int, int, int]):
        """
        Desenha glow atmosférico ao redor do sprite.
        
        Args:
            color: Cor do glow
        """
        glow_intensity = int(self.sprite_alpha * 0.3)
        if glow_intensity <= 0:
            return
        
        # Criar surface de glow
        glow_size = (self.sprite_rect.width + 40, self.sprite_rect.height + 40)
        glow_surface = pygame.Surface(glow_size, pygame.SRCALPHA)
        
        # Desenhar glow difuso
        center = (glow_size[0] // 2, glow_size[1] // 2)
        
        for i in range(20):
            alpha = max(0, glow_intensity - i * 3)
            if alpha > 0:
                color_alpha = (*color, alpha)
                pygame.draw.ellipse(
                    glow_surface,
                    color_alpha,
                    (center[0] - self.sprite_rect.width//2 - i,
                     center[1] - self.sprite_rect.height//2 - i,
                     self.sprite_rect.width + i*2,
                     self.sprite_rect.height + i*2)
                )
        
        # Posicionar glow
        glow_rect = glow_surface.get_rect(center=self.sprite_rect.center)
        self.screen.blit(glow_surface, glow_rect, special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def _draw_info_panel(self):
        """Desenha painel de informações semi-transparente."""
        if self.panel_alpha <= 0:
            return
        
        character = self.characters[self.current_character_index]
        
        # Criar surface do painel
        panel_surface = pygame.Surface((self.panel_rect.width, self.panel_rect.height), pygame.SRCALPHA)
        
        # Background semi-transparente
        panel_bg_alpha = int(self.panel_alpha * 0.8)
        panel_surface.fill((0, 0, 0, panel_bg_alpha))
        
        # Bordas arredondadas (simulação)
        pygame.draw.rect(panel_surface, (40, 40, 40, panel_bg_alpha), panel_surface.get_rect(), border_radius=8)
        
        # Aplicar alpha geral
        if self.panel_alpha < 255:
            panel_surface.set_alpha(int(self.panel_alpha))
        
        # Desenhar painel
        self.screen.blit(panel_surface, self.panel_rect)
        
        # Desenhar conteúdo do painel
        self._draw_panel_content(character)
    
    def _draw_panel_content(self, character: CharacterData):
        """
        Desenha conteúdo do painel de informações.
        
        Args:
            character: Dados do personagem
        """
        if self.panel_alpha <= 0:
            return
        
        # Fontes
        title_font = theme.typography.get_font('title_medium')
        subtitle_font = theme.typography.get_font('body_large')
        body_font = theme.typography.get_font('body_medium')
        
        # Posições
        content_x = self.panel_rect.x + 30
        current_y = self.panel_rect.y + 30
        content_width = self.panel_rect.width - 60
        
        # Nome do personagem
        title_color = character.color_theme
        title_surface = title_font.render(character.name, True, title_color)
        if self.panel_alpha < 255:
            title_surface.set_alpha(int(self.panel_alpha))
        self.screen.blit(title_surface, (content_x, current_y))
        current_y += title_surface.get_height() + 10
        
        # Subtítulo
        subtitle_surface = subtitle_font.render(character.subtitle, True, theme.colors.PARCHMENT)
        if self.panel_alpha < 255:
            subtitle_surface.set_alpha(int(self.panel_alpha))
        self.screen.blit(subtitle_surface, (content_x, current_y))
        current_y += subtitle_surface.get_height() + 20
        
        # Aba "HISTÓRIA"
        tab_surface = body_font.render("HISTÓRIA", True, theme.colors.GOLD_PRIMARY)
        if self.panel_alpha < 255:
            tab_surface.set_alpha(int(self.panel_alpha))
        self.screen.blit(tab_surface, (content_x, current_y))
        
        # Underline animado
        underline_width = int(tab_surface.get_width() * (self.panel_alpha / 255))
        pygame.draw.line(
            self.screen,
            theme.colors.GOLD_PRIMARY,
            (content_x, current_y + tab_surface.get_height() + 2),
            (content_x + underline_width, current_y + tab_surface.get_height() + 2),
            2
        )
        current_y += tab_surface.get_height() + 15
        
        # Descrição (quebra de linha)
        self._draw_wrapped_text(character.description, body_font, theme.colors.PARCHMENT,
                               content_x, current_y, content_width, 3)
        current_y += 120  # Espaço estimado para 3 linhas
        
        # Atributos
        self._draw_attributes(character, content_x, current_y, content_width)
    
    def _draw_wrapped_text(self, text: str, font: pygame.font.Font, color: Tuple[int, int, int],
                          x: int, y: int, max_width: int, max_lines: int):
        """
        Desenha texto com quebra de linha.
        
        Args:
            text: Texto a desenhar
            font: Fonte
            color: Cor do texto
            x, y: Posição
            max_width: Largura máxima
            max_lines: Número máximo de linhas
        """
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                
                if len(lines) >= max_lines:
                    break
        
        if current_line and len(lines) < max_lines:
            lines.append(' '.join(current_line))
        
        # Desenhar linhas
        for i, line in enumerate(lines[:max_lines]):
            line_surface = font.render(line, True, color)
            if self.panel_alpha < 255:
                line_surface.set_alpha(int(self.panel_alpha))
            self.screen.blit(line_surface, (x, y + i * (font.get_height() + 5)))
    
    def _draw_attributes(self, character: CharacterData, x: int, y: int, width: int):
        """
        Desenha barras de atributos estilizadas.
        
        Args:
            character: Dados do personagem
            x, y: Posição inicial
            width: Largura disponível
        """
        if self.attributes_alpha <= 0:
            return
        
        attr_font = theme.typography.get_font('body_small')
        bar_height = 20
        bar_spacing = 30
        
        # Título da seção
        attr_title = attr_font.render("ATRIBUTOS", True, theme.colors.GOLD_PRIMARY)
        if self.attributes_alpha < 255:
            attr_title.set_alpha(int(self.attributes_alpha))
        self.screen.blit(attr_title, (x, y))
        y += attr_title.get_height() + 15
        
        # Desenhar cada atributo
        max_value = 40  # Valor máximo para cálculo da barra
        
        for i, (attr_name, attr_value) in enumerate(character.attributes.items()):
            attr_y = y + i * bar_spacing
            
            # Nome do atributo
            name_surface = attr_font.render(f"{attr_name}: {attr_value}", True, theme.colors.PARCHMENT)
            if self.attributes_alpha < 255:
                name_surface.set_alpha(int(self.attributes_alpha))
            self.screen.blit(name_surface, (x, attr_y))
            
            # Barra de atributo
            bar_x = x + 120
            bar_width = width - 130
            
            # Background da barra (textura riscada simulada)
            bar_bg = pygame.Rect(bar_x, attr_y + 3, bar_width, bar_height - 6)
            pygame.draw.rect(self.screen, (40, 40, 40), bar_bg, border_radius=3)
            
            # Preenchimento animado
            fill_percentage = (attr_value / max_value) * (self.attributes_alpha / 255)
            fill_width = int(bar_width * fill_percentage)
            
            if fill_width > 0:
                fill_rect = pygame.Rect(bar_x, attr_y + 3, fill_width, bar_height - 6)
                pygame.draw.rect(self.screen, character.color_theme, fill_rect, border_radius=3)
                
                # Brilho na barra
                highlight_rect = pygame.Rect(bar_x, attr_y + 3, fill_width, 3)
                highlight_color = tuple(min(255, c + 50) for c in character.color_theme)
                pygame.draw.rect(self.screen, highlight_color, highlight_rect, border_radius=3)
    
    def get_selected_character(self) -> str:
        """Retorna ID do personagem atualmente selecionado."""
        return self.characters[self.current_character_index].id
