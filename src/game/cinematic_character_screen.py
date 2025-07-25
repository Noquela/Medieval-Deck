"""
Tela de seleção de personagem cinematográfica para Medieval Deck.

Implementa design moderno com:
- Backgrounds cinematográficos gerados por IA
- Sprites de personagens transparentes
- Animações suaves de transição
- Sistema de partículas por personagem
- UI componentizada com botões animados
- Layout responsivo para ultrawide 3440x1440
"""

import pygame
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from ..ui.theme import theme, draw_text_with_shadow
from ..ui.animation import animation_manager, animate_to, EasingType, fade_in, fade_out
from ..ui.particles import particle_manager, ParticleEmitter, ParticleType
from ..components.button import Button, IconButton
from ..generators.asset_generator import AssetGenerator

logger = logging.getLogger(__name__)


class CharacterData:
    """Dados de um personagem para a tela de seleção."""
    
    def __init__(self, character_id: str, name: str, description: str, stats: Dict[str, int]):
        self.id = character_id
        self.name = name  
        self.description = description
        self.stats = stats
        
        # Assets visuais
        self.background_surface: Optional[pygame.Surface] = None
        self.sprite_surface: Optional[pygame.Surface] = None
        
        # Efeitos de partículas
        self.particle_emitter: Optional[ParticleEmitter] = None
        
        # Estado de animação
        self.alpha = 255
        self.sprite_scale = 1.0
        self.sprite_x_offset = 0.0


class CinematicCharacterSelectionScreen:
    """
    Tela de seleção de personagem com design cinematográfico AAA.
    
    Features:
    - Backgrounds 4K cinematográficos únicos por personagem
    - Sprites transparentes animados
    - Transições suaves com cross-fade
    - Sistema de partículas atmosféricas
    - UI moderna com botões animados
    - Layout otimizado para ultrawide
    """
    
    def __init__(self, screen: pygame.Surface, config, asset_generator: Optional[AssetGenerator] = None):
        self.screen = screen
        self.config = config
        self.asset_generator = asset_generator
        
        # Dimensões da tela
        self.screen_width = config.ui.window_width
        self.screen_height = config.ui.window_height
        
        # Dados dos personagens
        self.characters: Dict[str, CharacterData] = {}
        self.character_order = ["knight", "wizard", "assassin"]
        self.current_character_index = 0
        
        # Estado da tela
        self.is_transitioning = False
        self.transition_alpha = 0
        self.selected_character = None
        
        # UI Components
        self.navigation_buttons: Dict[str, Button] = {}
        self.select_button: Optional[Button] = None
        self.back_button: Optional[Button] = None
        
        # Superfícies de transição
        self.transition_surface: Optional[pygame.Surface] = None
        self.overlay_surface: Optional[pygame.Surface] = None
        
        # Timeline de animações
        self.intro_animations_complete = False
        
        # Inicialização
        self._setup_characters()
        self._setup_ui_components()
        self._load_assets()
        
        logger.info("Cinematic character selection screen initialized")
    
    def _setup_characters(self):
        """Configura dados dos personagens."""
        character_configs = {
            "knight": {
                "name": "Cavaleiro Valente",
                "description": "Guerreiro nobre com força incomparável e honra inabalável. Especialista em combate corpo a corpo e proteção de aliados.",
                "stats": {"Força": 9, "Defesa": 8, "Magia": 3, "Velocidade": 5}
            },
            "wizard": {
                "name": "Mestre Arcano", 
                "description": "Sábio dos mistérios arcanos, domina magias poderosas e conhece segredos antigos. Frágil mas devastador.",
                "stats": {"Força": 3, "Defesa": 4, "Magia": 10, "Velocidade": 6}
            },
            "assassin": {
                "name": "Assassino das Sombras",
                "description": "Mestre das sombras, move-se silenciosamente e ataca com precisão letal. Velocidade e furtividade são suas armas.",
                "stats": {"Força": 6, "Defesa": 5, "Magia": 4, "Velocidade": 10}
            }
        }
        
        for char_id, config in character_configs.items():
            self.characters[char_id] = CharacterData(
                char_id, config["name"], config["description"], config["stats"]
            )
    
    def _setup_ui_components(self):
        """Configura componentes de interface."""
        # Botões de navegação (setas)
        button_size = 80
        button_y = self.screen_height // 2 - button_size // 2
        
        # Ícones de seta (temporários - serão substituídos por IA)
        left_arrow = self._create_temp_arrow_icon("left")
        right_arrow = self._create_temp_arrow_icon("right")
        
        self.navigation_buttons["left"] = IconButton(
            50, button_y, button_size, left_arrow, self._previous_character
        )
        
        self.navigation_buttons["right"] = IconButton(
            self.screen_width - 50 - button_size, button_y, button_size, 
            right_arrow, self._next_character
        )
        
        # Botão de seleção
        select_button_width = 200
        select_button_height = 60
        select_x = self.screen_width - select_button_width - 50
        select_y = self.screen_height - 150
        
        self.select_button = Button(
            select_x, select_y, select_button_width, select_button_height,
            "SELECIONAR", "button", self._select_character, "primary"
        )
        
        # Botão voltar
        back_button_width = 150
        back_x = 50
        back_y = self.screen_height - 150
        
        self.back_button = Button(
            back_x, back_y, back_button_width, select_button_height,
            "VOLTAR", "button", self._go_back, "secondary"
        )
    
    def _create_temp_arrow_icon(self, direction: str) -> pygame.Surface:
        """Cria ícone temporário de seta até os assets de IA serem gerados."""
        size = 64
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Cor dourada
        color = theme.colors.GOLD_PRIMARY
        
        # Desenha seta simples
        center_x, center_y = size // 2, size // 2
        
        if direction == "left":
            points = [
                (center_x + 15, center_y - 20),
                (center_x - 15, center_y),
                (center_x + 15, center_y + 20)
            ]
        else:  # right
            points = [
                (center_x - 15, center_y - 20),
                (center_x + 15, center_y),
                (center_x - 15, center_y + 20)
            ]
        
        pygame.draw.polygon(surface, color, points)
        return surface
    
    def _load_assets(self):
        """Carrega assets cinematográficos."""
        assets_path = Path(self.config.assets_generated_dir)
        
        # Carrega backgrounds cinematográficos
        for char_id in self.character_order:
            char_data = self.characters[char_id]
            
            # Background específico
            bg_path = assets_path / f"{char_id}_cinematic.png"
            if bg_path.exists():
                try:
                    char_data.background_surface = pygame.image.load(str(bg_path)).convert()
                    logger.info(f"Background cinematográfico carregado para {char_id}")
                except Exception as e:
                    logger.warning(f"Erro ao carregar background {bg_path}: {e}")
                    char_data.background_surface = self._create_fallback_background(char_id)
            else:
                logger.warning(f"Background cinematográfico não encontrado: {bg_path}")
                char_data.background_surface = self._create_fallback_background(char_id)
            
            # Sprite do personagem
            sprite_path = assets_path / f"{char_id}_sprite.png"
            if sprite_path.exists():
                try:
                    char_data.sprite_surface = pygame.image.load(str(sprite_path)).convert_alpha()
                    logger.info(f"Sprite carregado para {char_id}")
                except Exception as e:
                    logger.warning(f"Erro ao carregar sprite {sprite_path}: {e}")
                    char_data.sprite_surface = self._create_fallback_sprite(char_id)
            else:
                logger.warning(f"Sprite não encontrado: {sprite_path}")
                char_data.sprite_surface = self._create_fallback_sprite(char_id)
        
        # Configura sistema de partículas para cada personagem
        self._setup_particle_systems()
    
    def _create_fallback_background(self, char_id: str) -> pygame.Surface:
        """Cria background de fallback case o IA não esteja disponível."""
        surface = pygame.Surface((self.screen_width, self.screen_height))
        
        if char_id == "knight":
            surface.fill(theme.colors.GOLD_DARK)
        elif char_id == "wizard":
            surface.fill(theme.colors.PURPLE_MYSTICAL)
        else:  # assassin
            surface.fill(theme.colors.STONE_DARK)
        
        return surface
    
    def _create_fallback_sprite(self, char_id: str) -> pygame.Surface:
        """Cria sprite de fallback case o IA não esteja disponível."""
        surface = pygame.Surface((300, 450), pygame.SRCALPHA)
        
        if char_id == "knight":
            color = theme.colors.GOLD_PRIMARY
        elif char_id == "wizard":
            color = theme.colors.PURPLE_LIGHT
        else:  # assassin
            color = theme.colors.STONE_MEDIUM
        
        # Desenha forma simples representando personagem
        pygame.draw.ellipse(surface, color, (100, 50, 100, 150))  # Corpo
        pygame.draw.circle(surface, color, (150, 100), 40)        # Cabeça
        
        return surface
    
    def _setup_particle_systems(self):
        """Configura sistemas de partículas únicos por personagem."""
        for char_id in self.character_order:
            char_data = self.characters[char_id]
            
            if char_id == "knight":
                # Brasas de fogo para o cavaleiro
                char_data.particle_emitter = particle_manager.create_fire_emitters(
                    0, self.screen_height - 200, self.screen_width, 200
                )
            elif char_id == "wizard":
                # Pó mágico para o mago
                char_data.particle_emitter = particle_manager.create_magic_dust_emitter(
                    0, 0, self.screen_width, self.screen_height
                )
            else:  # assassin
                # Névoa para o assassino
                char_data.particle_emitter = particle_manager.create_mist_emitter(
                    0, self.screen_height - 300, self.screen_width, 300
                )
            
            # Inicia desativado
            char_data.particle_emitter.set_active(False)
    
    def _get_current_character(self) -> CharacterData:
        """Retorna dados do personagem atual."""
        char_id = self.character_order[self.current_character_index]
        return self.characters[char_id]
    
    def _previous_character(self):
        """Navega para o personagem anterior."""
        if not self.is_transitioning:
            self._change_character(-1)
    
    def _next_character(self):
        """Navega para o próximo personagem."""
        if not self.is_transitioning:
            self._change_character(1)
    
    def _change_character(self, direction: int):
        """
        Muda personagem com animação suave.
        
        Args:
            direction: -1 para anterior, 1 para próximo
        """
        if self.is_transitioning:
            return
        
        # Desativa partículas do personagem atual
        current_char = self._get_current_character()
        if current_char.particle_emitter:
            current_char.particle_emitter.set_active(False)
        
        # Calcula novo índice
        new_index = (self.current_character_index + direction) % len(self.character_order)
        
        # Inicia transição
        self.is_transitioning = True
        self.transition_alpha = 0
        
        # Animação de fade out
        animate_to(
            self, 'transition_alpha', 255, 0.3, EasingType.EASE_IN_OUT,
            on_complete=lambda: self._complete_character_transition(new_index)
        )
    
    def _complete_character_transition(self, new_index: int):
        """Completa transição entre personagens."""
        # Atualiza índice
        self.current_character_index = new_index
        
        # Ativa partículas do novo personagem
        new_char = self._get_current_character()
        if new_char.particle_emitter:
            new_char.particle_emitter.set_active(True)
        
        # Anima sprite entrando
        new_char.sprite_x_offset = 100 if new_index > 0 else -100
        animate_to(new_char, 'sprite_x_offset', 0, 0.4, EasingType.EASE_OUT_CUBIC)
        
        # Fade in
        animate_to(
            self, 'transition_alpha', 0, 0.3, EasingType.EASE_IN_OUT,
            on_complete=lambda: setattr(self, 'is_transitioning', False)
        )
    
    def _select_character(self) -> str:
        """Seleciona personagem atual."""
        current_char = self._get_current_character()
        self.selected_character = current_char.id
        logger.info(f"Personagem selecionado: {current_char.name}")
        
        # Efeito visual de seleção
        particle_manager.create_spark_burst(
            self.screen_width // 2, self.screen_height // 2, 20
        )
        
        # Retorna ação para o UI principal
        return f"select_{current_char.id}"
    
    def _go_back(self) -> str:
        """Volta para o menu principal."""
        logger.info("Voltando para menu principal")
        return "back_to_menu"
    
    def start_intro_animations(self):
        """Inicia animações de introdução da tela."""
        if self.intro_animations_complete:
            return
        
        # Fade in dos botões com delay escalonado
        for i, (button_id, button) in enumerate(self.navigation_buttons.items()):
            button.alpha = 0
            animate_to(button, 'alpha', 255, 0.4, EasingType.EASE_OUT, delay=i * 0.1)
        
        # Fade in dos botões de ação
        self.select_button.alpha = 0
        self.back_button.alpha = 0
        
        animate_to(self.select_button, 'alpha', 255, 0.4, EasingType.EASE_OUT, delay=0.3)
        animate_to(self.back_button, 'alpha', 255, 0.4, EasingType.EASE_OUT, delay=0.4)
        
        # Anima sprite do personagem inicial
        current_char = self._get_current_character()
        current_char.sprite_scale = 0.8
        animate_to(current_char, 'sprite_scale', 1.0, 0.6, EasingType.EASE_OUT_CUBIC, delay=0.2)
        
        # Ativa partículas do personagem inicial
        if current_char.particle_emitter:
            current_char.particle_emitter.set_active(True)
        
        self.intro_animations_complete = True
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Processa eventos de input.
        
        Args:
            event: Evento do pygame
            
        Returns:
            String de ação ou None se não processado
        """
        # Eventos de teclado
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self._previous_character()
                return None  # Navegação interna, sem ação externa
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self._next_character()
                return None  # Navegação interna, sem ação externa
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self._select_character()
            elif event.key == pygame.K_ESCAPE:
                return self._go_back()
        
        # Eventos dos botões
        for button in self.navigation_buttons.values():
            if button.handle_event(event):
                return None  # Navegação interna
        
        if self.select_button.handle_event(event):
            return self._select_character()
        
        if self.back_button.handle_event(event):
            return self._go_back()
        
        return None
    
    def update(self, dt: float):
        """
        Atualiza animações e estado da tela.
        
        Args:
            dt: Delta time em segundos
        """
        # Atualiza animações
        animation_manager.update()
        
        # Atualiza sistema de partículas
        particle_manager.update(dt)
        
        # Atualiza botões
        for button in self.navigation_buttons.values():
            button.update(dt)
        
        self.select_button.update(dt)
        self.back_button.update(dt)
        
        # Inicia animações de intro se necessário
        if not self.intro_animations_complete:
            self.start_intro_animations()
    
    def draw(self):
        """Desenha tela de seleção cinematográfica usando self.screen."""
        self.draw_on_surface(self.screen)
    
    def draw_on_surface(self, surface: pygame.Surface):
        """
        Desenha tela de seleção cinematográfica.
        
        Args:
            surface: Superfície de destino
        """
        current_char = self._get_current_character()
        
        # 1. Desenha background cinematográfico
        if current_char.background_surface:
            surface.blit(current_char.background_surface, (0, 0))
        
        # 2. Desenha efeitos de partículas (atrás do sprite)
        particle_manager.draw(surface)
        
        # 3. Desenha sprite do personagem
        self._draw_character_sprite(surface, current_char)
        
        # 4. Desenha overlay de transição se necessário
        if self.is_transitioning and self.transition_alpha > 0:
            overlay = pygame.Surface((self.screen_width, self.screen_height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.transition_alpha)
            surface.blit(overlay, (0, 0))
        
        # 5. Desenha informações do personagem
        self._draw_character_info(surface, current_char)
        
        # 6. Desenha botões de interface
        self._draw_ui_elements(surface)
    
    def _draw_character_sprite(self, surface: pygame.Surface, char_data: CharacterData):
        """Desenha sprite do personagem com animações."""
        if not char_data.sprite_surface:
            return
        
        sprite = char_data.sprite_surface
        
        # Aplica escala
        if char_data.sprite_scale != 1.0:
            new_size = (
                int(sprite.get_width() * char_data.sprite_scale),
                int(sprite.get_height() * char_data.sprite_scale)
            )
            sprite = pygame.transform.scale(sprite, new_size)
        
        # Posição centralizada na direita da tela
        sprite_x = self.screen_width - sprite.get_width() - 200 + char_data.sprite_x_offset
        sprite_y = self.screen_height - sprite.get_height() - 50
        
        surface.blit(sprite, (sprite_x, sprite_y))
    
    def _draw_character_info(self, surface: pygame.Surface, char_data: CharacterData):
        """Desenha informações do personagem (nome, descrição, stats)."""
        # Painel de informações (lado esquerdo)
        panel_x = 50
        panel_y = 100
        panel_width = 500
        panel_height = 400
        
        # Fundo do painel com transparência
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_color = (*theme.colors.SHADOW_BLACK, 180)
        pygame.draw.rect(panel_surface, panel_color, (0, 0, panel_width, panel_height))
        surface.blit(panel_surface, (panel_x, panel_y))
        
        # Nome do personagem
        name_font = theme.typography.get_font("title_medium")
        draw_text_with_shadow(
            surface, char_data.name, name_font,
            (panel_x + 20, panel_y + 20),
            theme.colors.GOLD_LIGHT
        )
        
        # Descrição
        desc_font = theme.typography.get_font("body_medium")
        self._draw_wrapped_text(
            surface, char_data.description, desc_font,
            (panel_x + 20, panel_y + 80),
            theme.colors.PARCHMENT,
            panel_width - 40
        )
        
        # Estatísticas
        stats_y = panel_y + 200
        stats_font = theme.typography.get_font("body_large")
        
        draw_text_with_shadow(
            surface, "ATRIBUTOS:", stats_font,
            (panel_x + 20, stats_y),
            theme.colors.GOLD_PRIMARY
        )
        
        # Barras de atributos
        for i, (stat_name, value) in enumerate(char_data.stats.items()):
            bar_y = stats_y + 40 + i * 35
            self._draw_stat_bar(
                surface, stat_name, value,
                (panel_x + 20, bar_y),
                panel_width - 40
            )
    
    def _draw_wrapped_text(self, surface: pygame.Surface, text: str, font: pygame.font.Font,
                          pos: Tuple[int, int], color: Tuple[int, int, int], max_width: int):
        """Desenha texto com quebra de linha."""
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
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Desenha linhas
        for i, line in enumerate(lines):
            line_y = pos[1] + i * (font.get_height() + 4)
            draw_text_with_shadow(surface, line, font, (pos[0], line_y), color)
    
    def _draw_stat_bar(self, surface: pygame.Surface, stat_name: str, value: int,
                      pos: Tuple[int, int], width: int):
        """Desenha barra de atributo animada."""
        bar_height = 20
        max_value = 10
        
        # Nome do atributo
        label_font = theme.typography.get_font("label")
        draw_text_with_shadow(
            surface, f"{stat_name}:", label_font,
            pos, theme.colors.PARCHMENT
        )
        
        # Posição da barra
        bar_x = pos[0] + 100
        bar_y = pos[1]
        bar_width = width - 120
        
        # Fundo da barra
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, theme.colors.STONE_DARK, bg_rect)
        
        # Barra de valor
        fill_width = int((value / max_value) * bar_width)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            
            # Cor baseada no valor
            if value >= 8:
                bar_color = theme.colors.GOLD_PRIMARY
            elif value >= 6:
                bar_color = theme.colors.GREEN_FOREST
            else:
                bar_color = theme.colors.STONE_MEDIUM
            
            pygame.draw.rect(surface, bar_color, fill_rect)
        
        # Borda da barra
        pygame.draw.rect(surface, theme.colors.GOLD_DARK, bg_rect, 2)
        
        # Valor numérico
        value_text = f"{value}/{max_value}"
        draw_text_with_shadow(
            surface, value_text, label_font,
            (bar_x + bar_width + 10, bar_y),
            theme.colors.PARCHMENT
        )
    
    def _draw_ui_elements(self, surface: pygame.Surface):
        """Desenha elementos de interface."""
        # Botões de navegação
        for button in self.navigation_buttons.values():
            button.draw(surface)
        
        # Botões de ação
        self.select_button.draw(surface)
        self.back_button.draw(surface)
        
        # Indicador de personagem atual
        self._draw_character_indicator(surface)
    
    def _draw_character_indicator(self, surface: pygame.Surface):
        """Desenha indicador de qual personagem está selecionado."""
        indicator_size = 12
        indicator_spacing = 30
        total_width = len(self.character_order) * indicator_spacing
        
        start_x = (self.screen_width - total_width) // 2
        indicator_y = self.screen_height - 50
        
        for i, char_id in enumerate(self.character_order):
            x = start_x + i * indicator_spacing
            
            if i == self.current_character_index:
                # Indicador ativo
                color = theme.colors.GOLD_PRIMARY
                size = indicator_size
            else:
                # Indicador inativo
                color = theme.colors.STONE_MEDIUM
                size = indicator_size - 3
            
            pygame.draw.circle(surface, color, (x, indicator_y), size)
            
            # Borda
            pygame.draw.circle(surface, theme.colors.PARCHMENT, (x, indicator_y), size, 2)
