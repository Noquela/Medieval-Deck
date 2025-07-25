"""
Medieval Deck - Combat Screen UI Profissional

Interface de combate cinematográfica com design moderno, animações fluidas e integração IA.
Implementa a Fase 4 do roadmap com experiência visual premium.
"""

import pygame
import logging
import math
import time
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

from ..core.turn_engine import Player
from ..gameplay.cards import Card, CardType
from ..gameplay.gameplay_engine import GameplayEngine
from ..enemies.smart_enemies import SmartEnemy
from ..enemies.intelligent_combat import IntelligentCombatEngine
from ..ui.theme import UITheme, theme
from ..ui.animation import AnimationManager, animation_manager, EasingType
from ..ui.particles import ParticleSystem, ParticleEmitter, ParticleType
from ..components.button import Button
from ..generators.asset_generator import AssetGenerator

logger = logging.getLogger(__name__)


class CombatState(Enum):
    """Estados da tela de combate."""
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn" 
    CARD_SELECTION = "card_selection"
    TARGET_SELECTION = "target_selection"
    ANIMATION = "animation"
    VICTORY = "victory"
    DEFEAT = "defeat"
    PAUSED = "paused"


class CombatZone:
    """Representa uma zona de combate com grid para cartas/inimigos."""
    
    def __init__(self, rect: pygame.Rect, grid_size: Tuple[int, int], zone_type: str):
        self.rect = rect
        self.grid_cols, self.grid_rows = grid_size
        self.zone_type = zone_type  # "player" ou "enemy"
        self.slots = []
        self.background_surface = None
        self.border_texture = None
        self._setup_grid()
        
    def _setup_grid(self):
        """Configura o grid de slots da zona."""
        slot_width = (self.rect.width - theme.spacing.MARGIN_LARGE * (self.grid_cols + 1)) // self.grid_cols
        slot_height = (self.rect.height - theme.spacing.MARGIN_MEDIUM * (self.grid_rows + 1)) // self.grid_rows
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x = self.rect.x + theme.spacing.MARGIN_LARGE + col * (slot_width + theme.spacing.MARGIN_LARGE)
                y = self.rect.y + theme.spacing.MARGIN_MEDIUM + row * (slot_height + theme.spacing.MARGIN_MEDIUM)
                
                slot = CombatSlot(x, y, slot_width, slot_height, len(self.slots))
                self.slots.append(slot)


class CombatSlot:
    """Slot individual para carta ou inimigo com animações."""
    
    def __init__(self, x: int, y: int, width: int, height: int, index: int):
        self.base_rect = pygame.Rect(x, y, width, height)
        self.rect = self.base_rect.copy()
        self.index = index
        self.entity = None  # Card ou Enemy
        self.is_hovered = False
        self.is_selected = False
        
        # Animações
        self.hover_offset_y = 0
        self.target_hover_y = 0
        self.glow_alpha = 0
        self.target_glow_alpha = 0
        self.scale = 1.0
        self.target_scale = 1.0
        
        # Estado de animação de tween para centro
        self.tween_active = False
        self.tween_start_pos = None
        self.tween_target_pos = None
        self.tween_progress = 0
        self.tween_duration = 300  # ms
        
    def update(self, dt: float):
        """Atualiza animações do slot."""
        # Animação de hover (y offset)
        if self.is_hovered:
            self.target_hover_y = -15
            self.target_glow_alpha = 255
            self.target_scale = 1.05
        else:
            self.target_hover_y = 0
            self.target_glow_alpha = 0
            self.target_scale = 1.0
            
        # Interpolação suave para hover
        self.hover_offset_y += (self.target_hover_y - self.hover_offset_y) * dt * 8
        self.glow_alpha += (self.target_glow_alpha - self.glow_alpha) * dt * 6
        self.scale += (self.target_scale - self.scale) * dt * 10
        
        # Atualizar posição do rect
        self.rect = self.base_rect.copy()
        self.rect.y += int(self.hover_offset_y)
        
        # Animação de tween para centro (quando carta é jogada)
        if self.tween_active:
            self.tween_progress += dt * 1000  # converter para ms
            progress = min(self.tween_progress / self.tween_duration, 1.0)
            
            # Easing out cubic
            eased_progress = 1 - (1 - progress) ** 3
            
            if self.tween_start_pos and self.tween_target_pos:
                current_x = self.tween_start_pos[0] + (self.tween_target_pos[0] - self.tween_start_pos[0]) * eased_progress
                current_y = self.tween_start_pos[1] + (self.tween_target_pos[1] - self.tween_start_pos[1]) * eased_progress
                self.rect.center = (int(current_x), int(current_y))
                
            if progress >= 1.0:
                self.tween_active = False
                
    def start_center_tween(self, screen_center: Tuple[int, int]):
        """Inicia animação de tween para o centro da tela."""
        self.tween_active = True
        self.tween_start_pos = self.rect.center
        self.tween_target_pos = screen_center
        self.tween_progress = 0
        
    def get_display_rect(self) -> pygame.Rect:
        """Retorna retângulo para desenho considerando escala."""
        if self.scale != 1.0:
            scaled_width = int(self.rect.width * self.scale)
            scaled_height = int(self.rect.height * self.scale)
            scaled_rect = pygame.Rect(0, 0, scaled_width, scaled_height)
            scaled_rect.center = self.rect.center
            return scaled_rect
        return self.rect

class CombatScreen:
    """
    Tela de combate profissional com design cinematográfico.
    
    Funcionalidades avançadas:
    - Background dinâmico com parallax
    - Zonas de combate organizadas em grid
    - Animações fluidas de hover/click
    - Painel de estado flutuante
    - Botões com texturas IA
    - Sistema de partículas
    - Transições suaves entre turnos
    """
    
    def __init__(self, screen: pygame.Surface, combat_engine: IntelligentCombatEngine, 
                 asset_generator: Optional[AssetGenerator] = None):
        """
        Inicializa a tela de combate profissional.
        
        Args:
            screen: Surface principal do pygame
            combat_engine: Engine de combate inteligente
            asset_generator: Gerador de assets IA (opcional)
        """
        self.screen = screen
        self.combat_engine = combat_engine
        self.asset_generator = asset_generator
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Estado da tela
        self.state = CombatState.PLAYER_TURN
        self.running = True
        self.selected_card: Optional[Card] = None
        self.targeted_enemy: Optional[SmartEnemy] = None
        
        # Mouse tracking para parallax
        self.mouse_pos = (0, 0)
        self.last_mouse_pos = (0, 0)
        
        # Assets IA carregados
        self.assets = {}
        
        # Inicialização dos componentes
        self._load_ia_assets()
        self._setup_zones()
        self._setup_buttons()
        self._setup_particles()
        self._setup_player_panel()
        self._generate_background()
        
        # Transições e overlays
        self.turn_transition_alpha = 0
        self.turn_transition_active = False
        self.turn_transition_timer = 0
        
        logger.info("Professional CombatScreen initialized")
        
    def _load_ia_assets(self):
        """Carrega todos os assets gerados por IA para a interface."""
        assets_dir = Path("assets/ia")
        
        # Lista de assets necessários
        asset_files = [
            "battlefield_background.png",
            "zone_panel_texture.png", 
            "zone_border_texture.png",
            "hp_bar_texture.png",
            "mana_bar_texture.png",
            "icon_card.png",
            "icon_pause.png",
            "button_idle.png",
            "button_hover.png", 
            "button_pressed.png",
            "panel_shadow.png"
        ]
        
        for asset_file in asset_files:
            asset_path = assets_dir / asset_file
            if asset_path.exists():
                try:
                    self.assets[asset_file.replace('.png', '')] = pygame.image.load(asset_path)
                    logger.debug(f"Loaded IA asset: {asset_file}")
                except pygame.error as e:
                    logger.warning(f"Failed to load IA asset {asset_file}: {e}")
            else:
                # Gerar asset com IA se não existir
                self._generate_missing_asset(asset_file)
    
    def _generate_missing_asset(self, asset_name: str):
        """Gera asset faltante usando IA."""
        if not self.asset_generator:
            logger.warning(f"Cannot generate {asset_name} - no AssetGenerator available")
            return
            
        # Prompts específicos para cada tipo de asset
        prompts = {
            "battlefield_background.png": "battlefield at dawn, misty hills, medieval tents, dramatic lighting, cinematic",
            "zone_panel_texture.png": "medieval wooden panel texture, ornate borders, aged wood",
            "zone_border_texture.png": "ornate medieval border, gold filigree, decorative frame",
            "hp_bar_texture.png": "red health bar texture, slightly scratched metal",
            "mana_bar_texture.png": "blue mana bar texture, magical energy, glowing",
            "icon_card.png": "medieval playing card icon, simple design, golden",
            "icon_pause.png": "pause icon, medieval style, stone texture",
            "button_idle.png": "medieval button texture, stone and gold, idle state",
            "button_hover.png": "medieval button texture, stone and gold, glowing hover",
            "button_pressed.png": "medieval button texture, stone and gold, pressed down",
            "panel_shadow.png": "soft black shadow, transparent edges, drop shadow"
        }
        
        if asset_name in prompts:
            try:
                # Gerar asset com prompts específicos
                logger.info(f"Generating missing asset: {asset_name}")
                # TODO: Implementar geração via asset_generator
                # Por enquanto, criar placeholder
                self._create_placeholder_asset(asset_name)
            except Exception as e:
                logger.error(f"Failed to generate {asset_name}: {e}")
                self._create_placeholder_asset(asset_name)
    
    def _create_placeholder_asset(self, asset_name: str):
        """Cria placeholder para asset faltante."""
        # Criar surface placeholder baseado no tipo
        if "background" in asset_name:
            surface = pygame.Surface((self.width, self.height))
            surface.fill((40, 30, 50))  # Cor placeholder escura
        elif "icon" in asset_name:
            surface = pygame.Surface((32, 32))
            surface.fill((200, 200, 200))
        else:
            surface = pygame.Surface((100, 100))
            surface.fill((100, 100, 100))
            
        self.assets[asset_name.replace('.png', '')] = surface
        
    def _setup_zones(self):
        """Configura as zonas de combate (inimigos e jogador)."""
        # Zona de inimigos (topo)
        enemy_zone_height = 300
        enemy_zone_rect = pygame.Rect(
            theme.spacing.MARGIN_LARGE,
            theme.spacing.MARGIN_LARGE, 
            self.width - theme.spacing.MARGIN_LARGE * 2,
            enemy_zone_height
        )
        self.enemy_zone = CombatZone(enemy_zone_rect, (2, 1), "enemy")
        
        # Zona do jogador (base)
        player_zone_height = 200
        player_zone_y = self.height - player_zone_height - theme.spacing.MARGIN_LARGE
        player_zone_rect = pygame.Rect(
            theme.spacing.MARGIN_LARGE,
            player_zone_y,
            self.width - theme.spacing.MARGIN_LARGE * 2, 
            player_zone_height
        )
        self.player_zone = CombatZone(player_zone_rect, (5, 1), "player")
        
        # Preencher slots com cartas e inimigos
        self._populate_zones()
        
    def _populate_zones(self):
        """Preenche as zonas com cartas e inimigos."""
        # Preencher zona do jogador com cartas da mão
        if hasattr(self.combat_engine, 'current_player'):
            player = self.combat_engine.current_player
            if hasattr(player, 'hand'):
                for i, card in enumerate(player.hand[:5]):  # Max 5 cartas visíveis
                    if i < len(self.player_zone.slots):
                        self.player_zone.slots[i].entity = card
        
        # Preencher zona de inimigos
        if hasattr(self.combat_engine, 'enemies'):
            for i, enemy in enumerate(self.combat_engine.enemies[:2]):  # Max 2 inimigos
                if i < len(self.enemy_zone.slots):
                    self.enemy_zone.slots[i].entity = enemy
    
    def _setup_buttons(self):
        """Configura os botões da interface."""
        # Botão End Turn - parte inferior direita
        button_width = 120
        button_height = 40
        self.end_turn_button = Button(
            x=self.width - button_width - theme.spacing.MARGIN_LARGE,
            y=self.height - button_height - theme.spacing.MARGIN_MEDIUM,
            width=button_width,
            height=button_height,
            text="End Turn",
            on_click=self._end_turn,
            style="medieval"
        )
        
        # Botão Pause - topo direito como IconButton
        icon_size = 32
        self.pause_button = Button(
            x=self.width - icon_size - theme.spacing.MARGIN_MEDIUM,
            y=theme.spacing.MARGIN_MEDIUM,
            width=icon_size,
            height=icon_size,
            text="",  # Sem texto, só ícone
            on_click=self._toggle_pause,
            style="icon"
        )
        
    def _setup_particles(self):
        """Configura o sistema de partículas."""
        self.particle_system = ParticleSystem()
        
        # Configurar emissores para diferentes efeitos
        # Criar emissor simples para efeitos de dano (será atualizado dinamicamente)
        self.damage_emitter = ParticleEmitter(
            x=0, y=0,  # Posição será atualizada dinamicamente
            width=50, height=50,  # Área de emissão
            particle_type=ParticleType.GOLDEN_SPARKS,  # Usar tipo que existe
            emission_rate=10.0,
            max_particles=50
        )
        
    def _setup_player_panel(self):
        """Configura o painel flutuante de estado do jogador."""
        panel_width = 300
        panel_height = 80
        
        # Posição centralizada na parte inferior
        self.player_panel_rect = pygame.Rect(
            (self.width - panel_width) // 2,
            self.height - panel_height - theme.spacing.MARGIN_SMALL,
            panel_width,
            panel_height
        )
        
        # Criar surface do painel com alpha
        self.player_panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        
    def _generate_background(self):
        """Gera ou carrega o background dinâmico."""
        if "battlefield_background" in self.assets:
            self.background = self.assets["battlefield_background"]
            # Redimensionar para fit screen se necessário
            if self.background.get_size() != (self.width, self.height):
                self.background = pygame.transform.scale(self.background, (self.width, self.height))
        else:
            # Criar background placeholder
            self.background = pygame.Surface((self.width, self.height))
            self.background.fill((20, 15, 30))  # Cor base escura
            
            # Adicionar gradiente simples
            for y in range(self.height):
                alpha = min(100, y // 5)
                color = (20 + alpha//4, 15 + alpha//6, 30 + alpha//3)
                pygame.draw.line(self.background, color, (0, y), (self.width, y))
    
    def update(self, dt: float):
        """
        Atualiza todos os componentes da tela de combate.
        
        Args:
            dt: Delta time em segundos
        """
        # Atualizar posição do mouse para parallax
        self.last_mouse_pos = self.mouse_pos
        self.mouse_pos = pygame.mouse.get_pos()
        
        # Atualizar animações das zonas
        for slot in self.player_zone.slots:
            slot.update(dt)
        for slot in self.enemy_zone.slots:
            slot.update(dt)
            
        # Atualizar botões
        self.end_turn_button.update(dt)
        self.pause_button.update(dt)
        
        # Atualizar sistema de partículas
        self.particle_system.update(dt)
        
        # Atualizar transições de turno
        if self.turn_transition_active:
            self.turn_transition_timer += dt
            # Animação de fade in/out: 0->0.5->0 em 400ms
            progress = self.turn_transition_timer / 0.4  # 400ms
            if progress <= 0.5:
                self.turn_transition_alpha = int(255 * progress * 2)  # 0 to 255 in first half
            elif progress <= 1.0:
                self.turn_transition_alpha = int(255 * (2 - progress * 2))  # 255 to 0 in second half
            else:
                self.turn_transition_active = False
                self.turn_transition_alpha = 0
                self.turn_transition_timer = 0
        
        # Atualizar estado do combate
        self._update_combat_state()
        
    def _update_combat_state(self):
        """Atualiza o estado interno do combate."""
        # Verificar se combate terminou
        if hasattr(self.combat_engine, 'is_game_over') and self.combat_engine.is_game_over():
            if hasattr(self.combat_engine, 'is_victory') and self.combat_engine.is_victory():
                self.state = CombatState.VICTORY
            else:
                self.state = CombatState.DEFEAT
                
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Processa eventos da tela de combate.
        
        Args:
            event: Evento do pygame
            
        Returns:
            String de ação se alguma ação deve ser executada, None caso contrário
        """
        if event.type == pygame.QUIT:
            self.running = False
            return "exit_combat"
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == CombatState.CARD_SELECTION:
                    self._cancel_card_selection()
                elif self.state == CombatState.TARGET_SELECTION:
                    self._cancel_target_selection()
                elif self.state == CombatState.PAUSED:
                    return "exit_combat"
                else:
                    self.state = CombatState.PAUSED
                return None
                
            elif event.key == pygame.K_SPACE:
                if self.state == CombatState.PLAYER_TURN:
                    self._end_turn()
                return None
                
            elif event.key == pygame.K_p:
                self._toggle_pause()
                return None
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_left_click(event.pos)
                return None
            elif event.button == 3:  # Right click
                self._handle_right_click(event.pos)
                return None
                
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)
            
        return None
        
    def _handle_left_click(self, pos: Tuple[int, int]):
        """Processa clique esquerdo na interface."""
        x, y = pos
        
        # Verificar clique nos botões
        if self.end_turn_button.rect.collidepoint(x, y):
            if self.state == CombatState.PLAYER_TURN:
                self._end_turn()
            return
            
        if self.pause_button.rect.collidepoint(x, y):
            self._toggle_pause()
            return
            
        # Verificar clique nas cartas do jogador
        if self.state == CombatState.PLAYER_TURN:
            for slot in self.player_zone.slots:
                if slot.entity and slot.get_display_rect().collidepoint(x, y):
                    self._select_card(slot)
                    return
                    
        # Verificar clique nos inimigos (para targeting)
        if self.state == CombatState.TARGET_SELECTION:
            for slot in self.enemy_zone.slots:
                if slot.entity and slot.rect.collidepoint(x, y):
                    self._target_enemy(slot)
                    return
                    
    def _handle_right_click(self, pos: Tuple[int, int]):
        """Processa clique direito (cancelar seleções)."""
        if self.state == CombatState.CARD_SELECTION:
            self._cancel_card_selection()
        elif self.state == CombatState.TARGET_SELECTION:
            self._cancel_target_selection()
            
    def _handle_mouse_motion(self, pos: Tuple[int, int]):
        """Processa movimento do mouse para hover effects."""
        x, y = pos
        
        # Atualizar hover das cartas do jogador
        for slot in self.player_zone.slots:
            slot.is_hovered = (slot.entity and 
                              slot.get_display_rect().collidepoint(x, y))
                              
        # Atualizar hover dos inimigos
        for slot in self.enemy_zone.slots:
            slot.is_hovered = (slot.entity and 
                              slot.rect.collidepoint(x, y))
                              
        # Atualizar hover dos botões
        self.end_turn_button.is_hovered = self.end_turn_button.rect.collidepoint(x, y)
        self.pause_button.is_hovered = self.pause_button.rect.collidepoint(x, y)
        
    def _select_card(self, slot: CombatSlot):
        """Seleciona uma carta para uso."""
        self.selected_card = slot.entity
        self.state = CombatState.CARD_SELECTION
        
        # Iniciar animação de tween para centro
        screen_center = (self.width // 2, self.height // 2)
        slot.start_center_tween(screen_center)
        
        # Se a carta não precisa de target, usar imediatamente
        if hasattr(self.selected_card, 'needs_target') and not self.selected_card.needs_target:
            self._use_card_no_target()
        else:
            self.state = CombatState.TARGET_SELECTION
            
    def _target_enemy(self, slot: CombatSlot):
        """Seleciona um inimigo como alvo."""
        if self.selected_card and self.state == CombatState.TARGET_SELECTION:
            self.targeted_enemy = slot.entity
            self._use_card_with_target(slot)
            
    def _use_card_no_target(self):
        """Usa carta que não precisa de alvo."""
        if self.selected_card:
            # Aplicar efeito da carta
            self._apply_card_effect(self.selected_card, None)
            self._finish_card_use()
            
    def _use_card_with_target(self, target_slot: CombatSlot):
        """Usa carta com alvo específico."""
        if self.selected_card and self.targeted_enemy:
            # Disparar partículas de dano no alvo
            self._trigger_damage_particles(target_slot.rect.center)
            
            # Aplicar efeito da carta
            self._apply_card_effect(self.selected_card, self.targeted_enemy)
            self._finish_card_use()
            
    def _apply_card_effect(self, card: Card, target):
        """Aplica o efeito da carta no combate."""
        try:
            # Usar o combat engine para aplicar a carta
            if hasattr(self.combat_engine, 'use_card'):
                self.combat_engine.use_card(card, target)
            logger.info(f"Applied card effect: {card} on {target}")
        except Exception as e:
            logger.error(f"Failed to apply card effect: {e}")
            
    def _finish_card_use(self):
        """Finaliza o uso da carta."""
        self.selected_card = None
        self.targeted_enemy = None
        self.state = CombatState.PLAYER_TURN
        
        # Repovoar zonas para refletir mudanças
        self._populate_zones()
        
    def _trigger_damage_particles(self, position: Tuple[int, int]):
        """Dispara partículas de dano na posição especificada."""
        self.damage_emitter.position = position
        self.particle_system.add_emitter(self.damage_emitter)
        
    def _cancel_card_selection(self):
        """Cancela seleção de carta."""
        self.selected_card = None
        self.state = CombatState.PLAYER_TURN
        
    def _cancel_target_selection(self):
        """Cancela seleção de alvo."""
        self.targeted_enemy = None
        self.state = CombatState.CARD_SELECTION
        
    def _end_turn(self):
        """Finaliza o turno do jogador."""
        try:
            # Trigger turn transition animation
            self._start_turn_transition()
            
            # Usar combat engine para processar fim de turno
            if hasattr(self.combat_engine, 'end_turn'):
                self.combat_engine.end_turn()
                
            self.state = CombatState.ENEMY_TURN
            logger.info("Player turn ended")
        except Exception as e:
            logger.error(f"Failed to end turn: {e}")
            
    def _start_turn_transition(self):
        """Inicia animação de transição de turno."""
        self.turn_transition_active = True
        self.turn_transition_timer = 0
        self.turn_transition_alpha = 0
        
    def _toggle_pause(self):
        """Alterna entre pausado e não pausado."""
        if self.state == CombatState.PAUSED:
            self.state = CombatState.PLAYER_TURN
        else:
            self.state = CombatState.PAUSED
            
    def draw(self):
        """
        Desenha toda a interface de combate profissional.
        
        Ordem de renderização:
        1. Background com parallax
        2. Zonas de combate
        3. Cartas e inimigos
        4. Painel do jogador
        5. Botões
        6. Partículas
        7. Overlays e transições
        """
        # 1. Background dinâmico com parallax
        self._draw_background_with_parallax()
        
        # 2. Zonas de combate
        self._draw_zones()
        
        # 3. Cartas e inimigos
        self._draw_cards()
        self._draw_enemies()
        
        # 4. Painel flutuante do jogador
        self._draw_player_panel()
        
        # 5. Botões
        self._draw_buttons()
        
        # 6. Sistema de partículas
        self._draw_particles()
        
        # 7. Overlays e estados especiais
        self._draw_overlays()
        
        # 8. Debug info (se ativo)
        if hasattr(self, 'debug_mode') and self.debug_mode:
            self._draw_debug_info()
            
    def _draw_background_with_parallax(self):
        """Desenha background com efeito parallax baseado no mouse."""
        # Calcular offset de parallax
        mouse_x, mouse_y = self.mouse_pos
        center_x, center_y = self.width // 2, self.height // 2
        
        # Parallax sutil - 2% de movimento
        parallax_strength = 0.02
        offset_x = (mouse_x - center_x) * parallax_strength
        offset_y = (mouse_y - center_y) * parallax_strength
        
        # Desenhar background com offset
        bg_rect = self.background.get_rect()
        bg_rect.center = (center_x + offset_x, center_y + offset_y)
        
        self.screen.blit(self.background, bg_rect)
        
        # Adicionar blur direcional sutil (simulado com transparência)
        blur_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        blur_overlay.fill((0, 0, 0, 10))  # Muito sutil
        self.screen.blit(blur_overlay, (0, 0))
        
    def _draw_zones(self):
        """Desenha as zonas de combate com painéis semi-transparentes."""
        # Zona de inimigos
        self._draw_zone_panel(self.enemy_zone.rect, "enemy")
        
        # Zona do jogador  
        self._draw_zone_panel(self.player_zone.rect, "player")
        
    def _draw_zone_panel(self, rect: pygame.Rect, zone_type: str):
        """
        Desenha painel semi-transparente para uma zona.
        
        Args:
            rect: Retângulo da zona
            zone_type: Tipo da zona ("enemy" ou "player")
        """
        # Criar surface semi-transparente
        panel_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Cor base baseada no tipo
        if zone_type == "enemy":
            base_color = (80, 40, 40, 120)  # Vermelho escuro
        else:
            base_color = (40, 40, 80, 120)  # Azul escuro
            
        panel_surface.fill(base_color)
        
        # Desenhar borda decorativa
        border_color = (200, 180, 100, 180)  # Dourado
        pygame.draw.rect(panel_surface, border_color, 
                        (0, 0, rect.width, rect.height), 3)
        
        # Adicionar textura se disponível
        if "zone_panel_texture" in self.assets:
            texture = self.assets["zone_panel_texture"]
            texture = pygame.transform.scale(texture, (rect.width, rect.height))
            texture.set_alpha(60)  # Muito sutil
            panel_surface.blit(texture, (0, 0))
            
        # Desenhar no screen
        self.screen.blit(panel_surface, rect.topleft)
        
    def _draw_cards(self):
        """Desenha todas as cartas na zona do jogador."""
        for slot in self.player_zone.slots:
            if slot.entity:
                self._draw_card_in_slot(slot)
                
    def _draw_card_in_slot(self, slot: CombatSlot):
        """
        Desenha uma carta individual com todas as animações.
        
        Args:
            slot: Slot contendo a carta
        """
        card = slot.entity
        display_rect = slot.get_display_rect()
        
        # Surface da carta
        card_surface = pygame.Surface((display_rect.width, display_rect.height), pygame.SRCALPHA)
        
        # Background da carta
        if slot.is_selected:
            bg_color = (100, 100, 150, 200)
        elif slot.is_hovered:
            bg_color = (80, 80, 120, 180)
        else:
            bg_color = (60, 60, 90, 160)
            
        card_surface.fill(bg_color)
        
        # Borda da carta
        border_color = (200, 180, 100) if slot.is_hovered else (150, 130, 80)
        pygame.draw.rect(card_surface, border_color, 
                        (0, 0, display_rect.width, display_rect.height), 2)
        
        # Glow effect durante hover
        if slot.is_hovered and slot.glow_alpha > 0:
            glow_surface = pygame.Surface((display_rect.width + 10, display_rect.height + 10), pygame.SRCALPHA)
            glow_color = (255, 215, 0, int(slot.glow_alpha * 0.3))  # Dourado pulsante
            pygame.draw.rect(glow_surface, glow_color, 
                           (0, 0, display_rect.width + 10, display_rect.height + 10), 5)
            
            glow_rect = glow_surface.get_rect()
            glow_rect.center = display_rect.center
            self.screen.blit(glow_surface, glow_rect.topleft)
        
        # Texto da carta
        if hasattr(card, 'name'):
            font = pygame.font.Font(None, 24)
            text_surface = font.render(card.name, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(display_rect.width//2, 20))
            card_surface.blit(text_surface, text_rect)
            
        # Custo da carta
        if hasattr(card, 'cost'):
            cost_font = pygame.font.Font(None, 20)
            cost_text = cost_font.render(str(card.cost), True, (100, 200, 255))
            card_surface.blit(cost_text, (5, 5))
            
        # Desenhar carta no screen
        self.screen.blit(card_surface, display_rect.topleft)
        
    def _draw_enemies(self):
        """Desenha todos os inimigos na zona de inimigos."""
        for slot in self.enemy_zone.slots:
            if slot.entity:
                self._draw_enemy_in_slot(slot)
                
    def _draw_enemy_in_slot(self, slot: CombatSlot):
        """
        Desenha um inimigo individual.
        
        Args:
            slot: Slot contendo o inimigo
        """
        enemy = slot.entity
        display_rect = slot.get_display_rect()
        
        # Verificação de segurança
        if display_rect is None:
            logger.warning(f"display_rect is None for slot: {slot}")
            return
        
        # Surface do inimigo
        enemy_surface = pygame.Surface((display_rect.width, display_rect.height), pygame.SRCALPHA)
        
        # Background do inimigo
        if slot.is_hovered:
            bg_color = (120, 60, 60, 180)
        else:
            bg_color = (90, 45, 45, 160)
            
        enemy_surface.fill(bg_color)
        
        # Borda
        border_color = (200, 100, 100) if slot.is_hovered else (150, 80, 80)
        pygame.draw.rect(enemy_surface, border_color,
                        (0, 0, display_rect.width, display_rect.height), 2)
        
        # Nome do inimigo
        if hasattr(enemy, 'name'):
            font = pygame.font.Font(None, 24)
            text_surface = font.render(enemy.name, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(display_rect.width//2, 20))
            enemy_surface.blit(text_surface, text_rect)
            
        # HP do inimigo
        if hasattr(enemy, 'hp') and hasattr(enemy, 'max_hp'):
            hp_width = display_rect.width - 20
            hp_height = 8
            hp_x = 10
            hp_y = display_rect.height - 20
            
            # Barra de HP
            hp_bg_rect = pygame.Rect(hp_x, hp_y, hp_width, hp_height)
            pygame.draw.rect(enemy_surface, (100, 0, 0), hp_bg_rect)
            
            hp_percent = enemy.hp / enemy.max_hp
            hp_fill_width = int(hp_width * hp_percent)
            hp_fill_rect = pygame.Rect(hp_x, hp_y, hp_fill_width, hp_height)
            pygame.draw.rect(enemy_surface, (200, 0, 0), hp_fill_rect)
            
            # Texto de HP
            hp_font = pygame.font.Font(None, 18)
            hp_text = hp_font.render(f"{enemy.hp}/{enemy.max_hp}", True, (255, 255, 255))
            enemy_surface.blit(hp_text, (hp_x, hp_y - 18))
            
        # Desenhar inimigo no screen
        self.screen.blit(enemy_surface, display_rect.topleft)
        
    def _draw_player_panel(self):
        """Desenha o painel flutuante de estado do jogador."""
        # Limpar surface do painel
        self.player_panel_surface.fill((0, 0, 0, 0))
        
        # Background do painel com transparência
        panel_bg = pygame.Surface((self.player_panel_rect.width, self.player_panel_rect.height), pygame.SRCALPHA)
        panel_bg.fill((40, 40, 60, 180))
        
        # Borda dourada
        pygame.draw.rect(panel_bg, (200, 180, 100, 200), 
                        (0, 0, self.player_panel_rect.width, self.player_panel_rect.height), 2)
        
        # Sombra (se asset disponível)
        if "panel_shadow" in self.assets:
            shadow = self.assets["panel_shadow"]
            shadow = pygame.transform.scale(shadow, 
                                          (self.player_panel_rect.width + 20, self.player_panel_rect.height + 20))
            shadow_rect = shadow.get_rect()
            shadow_rect.center = (self.player_panel_rect.centerx + 3, self.player_panel_rect.centery + 3)
            self.screen.blit(shadow, shadow_rect.topleft)
        
        self.player_panel_surface.blit(panel_bg, (0, 0))
        
        # Obter dados do jogador
        player = getattr(self.combat_engine, 'current_player', None)
        if player:
            self._draw_player_stats(player)
            
        # Desenhar painel no screen
        self.screen.blit(self.player_panel_surface, self.player_panel_rect.topleft)
        
    def _draw_player_stats(self, player):
        """Desenha as estatísticas do jogador no painel."""
        panel_width = self.player_panel_rect.width
        panel_height = self.player_panel_rect.height
        
        # HP Bar
        if hasattr(player, 'hp') and hasattr(player, 'max_hp'):
            hp_width = panel_width // 2 - 20
            hp_height = 12
            hp_x = 10
            hp_y = 15
            
            # Background da barra
            hp_bg = pygame.Rect(hp_x, hp_y, hp_width, hp_height)
            pygame.draw.rect(self.player_panel_surface, (60, 0, 0), hp_bg)
            
            # Preenchimento da barra
            hp_percent = player.hp / player.max_hp if player.max_hp > 0 else 0
            hp_fill_width = int(hp_width * hp_percent)
            hp_fill = pygame.Rect(hp_x, hp_y, hp_fill_width, hp_height)
            pygame.draw.rect(self.player_panel_surface, (200, 50, 50), hp_fill)
            
            # Texto HP
            font = pygame.font.Font(None, 20)
            hp_text = font.render(f"HP: {player.hp}/{player.max_hp}", True, (255, 255, 255))
            self.player_panel_surface.blit(hp_text, (hp_x, hp_y - 15))
            
        # Mana Bar
        if hasattr(player, 'mana') and hasattr(player, 'max_mana'):
            mana_width = panel_width // 2 - 20  
            mana_height = 12
            mana_x = panel_width // 2 + 10
            mana_y = 15
            
            # Background da barra
            mana_bg = pygame.Rect(mana_x, mana_y, mana_width, mana_height)
            pygame.draw.rect(self.player_panel_surface, (0, 0, 60), mana_bg)
            
            # Preenchimento da barra
            mana_percent = player.mana / player.max_mana if player.max_mana > 0 else 0
            mana_fill_width = int(mana_width * mana_percent)
            mana_fill = pygame.Rect(mana_x, mana_y, mana_fill_width, mana_height)
            pygame.draw.rect(self.player_panel_surface, (50, 50, 200), mana_fill)
            
            # Texto Mana
            mana_text = font.render(f"Mana: {player.mana}/{player.max_mana}", True, (255, 255, 255))
            self.player_panel_surface.blit(mana_text, (mana_x, mana_y - 15))
            
        # Informações de cartas
        deck_count = len(getattr(player, 'deck', []))
        hand_count = len(getattr(player, 'hand', []))
        
        info_font = pygame.font.Font(None, 18)
        deck_text = info_font.render(f"Deck: {deck_count}", True, (200, 200, 200))
        hand_text = info_font.render(f"Hand: {hand_count}", True, (200, 200, 200))
        
        self.player_panel_surface.blit(deck_text, (10, panel_height - 25))
        self.player_panel_surface.blit(hand_text, (80, panel_height - 25))
        
        # Ícone de carta (se disponível)
        if "icon_card" in self.assets:
            icon = self.assets["icon_card"]
            icon = pygame.transform.scale(icon, (16, 16))
            self.player_panel_surface.blit(icon, (panel_width - 25, panel_height - 25))
            
    def _draw_buttons(self):
        """Desenha todos os botões da interface."""
        # End Turn button
        self.end_turn_button.draw(self.screen)
        
        # Pause button  
        self.pause_button.draw(self.screen)
        
        # Adicionar ícone de pause se disponível
        if "icon_pause" in self.assets:
            pause_icon = self.assets["icon_pause"]
            pause_icon = pygame.transform.scale(pause_icon, (24, 24))
            icon_rect = pause_icon.get_rect()
            icon_rect.center = self.pause_button.rect.center
            self.screen.blit(pause_icon, icon_rect.topleft)
            
    def _draw_particles(self):
        """Desenha o sistema de partículas."""
        self.particle_system.draw(self.screen)
        
    def _draw_overlays(self):
        """Desenha overlays e transições especiais."""
        # Overlay de transição de turno
        if self.turn_transition_active and self.turn_transition_alpha > 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, self.turn_transition_alpha))
            self.screen.blit(overlay, (0, 0))
            
            # Texto de transição
            if self.turn_transition_alpha > 100:
                font = pygame.font.Font(None, 48)
                text = font.render("Enemy Turn", True, (255, 255, 255))
                text_rect = text.get_rect(center=(self.width//2, self.height//2))
                self.screen.blit(text, text_rect)
                
        # Overlay de pause
        if self.state == CombatState.PAUSED:
            pause_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pause_overlay.fill((0, 0, 0, 100))
            self.screen.blit(pause_overlay, (0, 0))
            
            # Texto de pause
            font = pygame.font.Font(None, 64)
            pause_text = font.render("PAUSED", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=(self.width//2, self.height//2))
            self.screen.blit(pause_text, text_rect)
            
            # Instrução
            inst_font = pygame.font.Font(None, 24)
            inst_text = inst_font.render("Press ESC to exit or P to resume", True, (200, 200, 200))
            inst_rect = inst_text.get_rect(center=(self.width//2, self.height//2 + 50))
            self.screen.blit(inst_text, inst_rect)
            
    def _draw_debug_info(self):
        """Desenha informações de debug."""
        debug_font = pygame.font.Font(None, 20)
        
        debug_lines = [
            f"State: {self.state.value}",
            f"Mouse: {self.mouse_pos}",
            f"Selected Card: {self.selected_card}",
            f"Targeted Enemy: {self.targeted_enemy}",
            f"Turn Transition: {self.turn_transition_active}"
        ]
        
        for i, line in enumerate(debug_lines):
            debug_surface = debug_font.render(line, True, (255, 255, 0))
            self.screen.blit(debug_surface, (10, 10 + i * 22))
