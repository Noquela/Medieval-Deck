"""
Medieval Deck - Combat Screen UI

Interface principal para combate com cartas, inimigos inteligentes e efeitos visuais.
Implementa a Fase 4 do roadmap - Interface e UX.
"""

import pygame
import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from ..core.turn_engine import Player
from ..gameplay.cards import Card, CardType
from ..gameplay.gameplay_engine import GameplayEngine
from ..enemies.smart_enemies import SmartEnemy
from ..enemies.intelligent_combat import IntelligentCombatEngine
from .theme import UITheme
from .animation import AnimationManager
from .particles import ParticleSystem

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


class CardSlot:
    """Representa um slot de carta na mão do jogador."""
    
    def __init__(self, x: int, y: int, width: int, height: int, index: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.index = index
        self.card: Optional[Card] = None
        self.is_hovered = False
        self.is_selected = False
        self.hover_offset = 0
        self.target_offset = 0
        
    def update(self, dt: float):
        """Atualiza animações do slot."""
        # Animação suave de hover
        if self.is_hovered:
            self.target_offset = -20
        else:
            self.target_offset = 0
            
        # Interpolação suave
        diff = self.target_offset - self.hover_offset
        self.hover_offset += diff * dt * 8
        
    def get_display_rect(self) -> pygame.Rect:
        """Retorna o rect com offset de hover aplicado."""
        rect = self.rect.copy()
        rect.y += int(self.hover_offset)
        return rect


class EnemySlot:
    """Representa um slot de inimigo na tela."""
    
    def __init__(self, x: int, y: int, width: int, height: int, index: int):
        self.rect = pygame.Rect(x, y, width, height)
        self.index = index
        self.enemy: Optional[SmartEnemy] = None
        self.is_hovered = False
        self.is_targeted = False
        self.damage_text_timer = 0
        self.damage_amount = 0
        
    def update(self, dt: float):
        """Atualiza animações do slot."""
        if self.damage_text_timer > 0:
            self.damage_text_timer -= dt


class CombatScreen:
    """
    Tela principal de combate com interface completa.
    
    Funcionalidades:
    - Visualização de cartas na mão
    - Seleção e uso de cartas
    - Visualização de inimigos
    - Sistema de targeting
    - Animações de combate
    - Indicadores de status
    - Interface de informações
    """
    
    def __init__(self, screen: pygame.Surface, combat_engine: IntelligentCombatEngine):
        self.screen = screen
        self.combat_engine = combat_engine
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Estado da tela
        self.state = CombatState.PLAYER_TURN
        self.running = True
        self.selected_card: Optional[Card] = None
        self.targeted_enemy: Optional[SmartEnemy] = None
        
        # Configurações de layout
        self.card_width = 120
        self.card_height = 180
        self.card_spacing = 10
        self.hand_y = self.height - self.card_height - 20
        
        self.enemy_width = 150
        self.enemy_height = 200
        self.enemy_spacing = 20
        self.enemy_y = 50
        
        # Slots para cartas e inimigos
        self.card_slots: List[CardSlot] = []
        self.enemy_slots: List[EnemySlot] = []
        
        # Sistemas visuais
        self.theme = UITheme()
        self.animation_manager = AnimationManager()
        self.particle_system = ParticleSystem()
        
        # Interface elements
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # Botões
        self.end_turn_button = pygame.Rect(self.width - 150, self.height - 60, 130, 40)
        self.pause_button = pygame.Rect(20, 20, 80, 40)
        
        # Inicializar layout
        self._setup_layout()
        self._sync_with_engine()
        
        logger.info("Combat screen initialized")
        
    def _setup_layout(self):
        """Configura o layout inicial da tela."""
        # Configurar slots de cartas na mão
        max_hand_size = 7  # Máximo de cartas na mão
        total_hand_width = (self.card_width * max_hand_size + 
                           self.card_spacing * (max_hand_size - 1))
        hand_start_x = (self.width - total_hand_width) // 2
        
        for i in range(max_hand_size):
            x = hand_start_x + i * (self.card_width + self.card_spacing)
            slot = CardSlot(x, self.hand_y, self.card_width, self.card_height, i)
            self.card_slots.append(slot)
            
        # Configurar slots de inimigos
        max_enemies = 4  # Máximo de inimigos visíveis
        total_enemy_width = (self.enemy_width * max_enemies + 
                            self.enemy_spacing * (max_enemies - 1))
        enemy_start_x = (self.width - total_enemy_width) // 2
        
        for i in range(max_enemies):
            x = enemy_start_x + i * (self.enemy_width + self.enemy_spacing)
            slot = EnemySlot(x, self.enemy_y, self.enemy_width, self.enemy_height, i)
            self.enemy_slots.append(slot)
            
    def _sync_with_engine(self):
        """Sincroniza o estado da UI com o engine de combate."""
        # Sincronizar cartas na mão
        hand = self.combat_engine.get_playable_cards()
        for i, slot in enumerate(self.card_slots):
            if i < len(hand):
                slot.card = hand[i]
            else:
                slot.card = None
                
        # Sincronizar inimigos
        enemies = self.combat_engine.get_alive_enemies()
        for i, slot in enumerate(self.enemy_slots):
            if i < len(enemies):
                slot.enemy = enemies[i]
            else:
                slot.enemy = None
                
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Processa eventos da tela de combate.
        
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
                    # Sair do combate
                    return "exit_combat"
                else:
                    self.state = CombatState.PAUSED
                return None
                
            elif event.key == pygame.K_SPACE:
                if self.state == CombatState.PLAYER_TURN:
                    self._end_player_turn()
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
        
    def _handle_left_click(self, pos: Tuple[int, int]) -> None:
        """Processa clique esquerdo."""
        x, y = pos
        
        # Verificar clique em botões
        if self.end_turn_button.collidepoint(x, y):
            if self.state == CombatState.PLAYER_TURN:
                self._end_player_turn()
            return
            
        if self.pause_button.collidepoint(x, y):
            self.state = CombatState.PAUSED
            return
            
        # Verificar clique em cartas
        if self.state == CombatState.PLAYER_TURN:
            for slot in self.card_slots:
                if slot.card and slot.get_display_rect().collidepoint(x, y):
                    self._select_card(slot.card)
                    return
                    
        # Verificar clique em inimigos (para targeting)
        if self.state == CombatState.TARGET_SELECTION:
            for slot in self.enemy_slots:
                if slot.enemy and slot.rect.collidepoint(x, y):
                    self._target_enemy(slot.enemy)
                    return
        
    def _handle_right_click(self, pos: Tuple[int, int]) -> None:
        """Processa clique direito (cancelar seleções)."""
        if self.state == CombatState.CARD_SELECTION:
            self._cancel_card_selection()
        elif self.state == CombatState.TARGET_SELECTION:
            self._cancel_target_selection()
        
    def _handle_mouse_motion(self, pos: Tuple[int, int]):
        """Processa movimento do mouse."""
        x, y = pos
        
        # Atualizar hover das cartas
        for slot in self.card_slots:
            slot.is_hovered = (slot.card and 
                              slot.get_display_rect().collidepoint(x, y))
                              
        # Atualizar hover dos inimigos
        for slot in self.enemy_slots:
            slot.is_hovered = (slot.enemy and 
                              slot.rect.collidepoint(x, y))
                              
    def _select_card(self, card: Card):
        """Seleciona uma carta para uso."""
        self.selected_card = card
        
        # Verificar se a carta precisa de alvo
        if card.card_type in [CardType.CREATURE, CardType.SPELL]:
            # Algumas cartas podem precisar de targeting
            alive_enemies = self.combat_engine.get_alive_enemies()
            if alive_enemies and card.card_type == CardType.SPELL:
                self.state = CombatState.TARGET_SELECTION
                logger.info(f"Card {card.name} selected, waiting for target")
            else:
                # Usar carta sem alvo específico
                self._use_card(card, None)
        else:
            # Usar carta diretamente
            self._use_card(card, None)
            
    def _target_enemy(self, enemy: SmartEnemy):
        """Seleciona um inimigo como alvo."""
        if self.selected_card:
            self._use_card(self.selected_card, [enemy])
            
    def _use_card(self, card: Card, targets: List[Any]):
        """Usa uma carta selecionada."""
        try:
            success = self.combat_engine.play_card(card, targets)
            if success:
                logger.info(f"Card {card.name} used successfully")
                
                # Criar efeito visual
                self._create_card_effect(card, targets)
                
                # Verificar fim de jogo
                if self.combat_engine.is_game_over():
                    victory_condition = self.combat_engine.get_victory_condition()
                    if victory_condition == "player_victory":
                        self.state = CombatState.VICTORY
                    else:
                        self.state = CombatState.DEFEAT
                else:
                    # Atualizar estado da UI
                    self._sync_with_engine()
                    
            else:
                logger.warning(f"Failed to use card {card.name}")
                
        except Exception as e:
            logger.error(f"Error using card {card.name}: {e}")
            
        finally:
            # Limpar seleções
            self.selected_card = None
            self.targeted_enemy = None
            self.state = CombatState.PLAYER_TURN
            
    def _create_card_effect(self, card: Card, targets: List[Any]):
        """Cria efeitos visuais para uso de carta."""
        # Aqui podemos adicionar partículas, animações, etc.
        if targets:
            for target in targets:
                if isinstance(target, SmartEnemy):
                    # Encontrar slot do inimigo
                    for slot in self.enemy_slots:
                        if slot.enemy == target:
                            # Criar efeito de dano
                            slot.damage_amount = card.cost * 2  # Exemplo
                            slot.damage_text_timer = 2.0
                            
                            # Adicionar partículas
                            center_x = slot.rect.centerx
                            center_y = slot.rect.centery
                            self.particle_system.create_impact_effect(center_x, center_y)
                            break
                            
    def _end_player_turn(self):
        """Finaliza o turno do jogador."""
        try:
            self.combat_engine.end_player_turn()
            self.state = CombatState.ENEMY_TURN
            self._sync_with_engine()
            logger.info("Player turn ended")
        except Exception as e:
            logger.error(f"Error ending player turn: {e}")
            
    def _cancel_card_selection(self):
        """Cancela a seleção de carta."""
        self.selected_card = None
        self.state = CombatState.PLAYER_TURN
        
    def _cancel_target_selection(self):
        """Cancela a seleção de alvo."""
        self.targeted_enemy = None
        self.state = CombatState.CARD_SELECTION
        
    def update(self, dt: float):
        """Atualiza o estado da tela de combate."""
        # Atualizar slots
        for slot in self.card_slots:
            slot.update(dt)
        for slot in self.enemy_slots:
            slot.update(dt)
            
        # Atualizar sistemas visuais
        self.animation_manager.update()
        self.particle_system.update(dt)
        
        # Processar turno dos inimigos
        if self.state == CombatState.ENEMY_TURN:
            # Simular processamento de IA (normalmente seria automático)
            # Por enquanto, vamos apenas voltar para o turno do jogador
            self.state = CombatState.PLAYER_TURN
            self._sync_with_engine()
            
    def draw(self):
        """Renderiza a tela de combate."""
        # Limpar tela com cor fixa para debug
        self.screen.fill((25, 25, 25))  # SHADOW_BLACK diretamente
        
        # Desenhar background
        self._draw_background()
        
        # Desenhar inimigos
        self._draw_enemies()
        
        # Desenhar cartas na mão
        self._draw_hand()
        
        # Desenhar informações do jogador
        self._draw_player_info()
        
        # Desenhar interface
        self._draw_ui_elements()
        
        # Desenhar efeitos visuais
        self.particle_system.draw(self.screen)
        
        # Desenhar estado específico
        self._draw_state_overlay()
        
    def _draw_background(self):
        """Desenha o background da tela."""
        # Por enquanto, um gradiente simples
        for y in range(self.height):
            progress = y / self.height
            color = (
                int(40 + progress * 20),
                int(20 + progress * 30),
                int(60 + progress * 40)
            )
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))
            
    def _draw_enemies(self):
        """Desenha os inimigos na tela."""
        for slot in self.enemy_slots:
            if not slot.enemy:
                continue
                
            enemy = slot.enemy
            rect = slot.rect
            
            # Background do slot
            color = (139, 0, 0)  # BLOOD_RED
            if slot.is_hovered:
                color = (180, 40, 40)  # Vermelho mais claro
            elif slot.is_targeted:
                color = (218, 165, 32)  # GOLD_PRIMARY
                
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (184, 134, 11), rect, 2)  # GOLD_DARK border
            
            # Nome do inimigo
            name_text = self.font_medium.render(enemy.name, True, (245, 245, 220))  # PARCHMENT
            name_rect = name_text.get_rect()
            name_rect.centerx = rect.centerx
            name_rect.y = rect.y + 10
            self.screen.blit(name_text, name_rect)
            
            # HP do inimigo
            hp_text = f"{enemy.hp}/{enemy.max_hp} HP"
            hp_surface = self.font_small.render(hp_text, True, (245, 245, 220))  # PARCHMENT
            hp_rect = hp_surface.get_rect()
            hp_rect.centerx = rect.centerx
            hp_rect.y = rect.bottom - 30
            self.screen.blit(hp_surface, hp_rect)
            
            # Barra de HP
            hp_bar_rect = pygame.Rect(rect.x + 10, rect.bottom - 20, rect.width - 20, 8)
            pygame.draw.rect(self.screen, (100, 100, 100), hp_bar_rect)
            
            hp_percentage = enemy.hp / enemy.max_hp
            hp_fill_width = int(hp_bar_rect.width * hp_percentage)
            hp_fill_rect = pygame.Rect(hp_bar_rect.x, hp_bar_rect.y, hp_fill_width, hp_bar_rect.height)
            
            hp_color = (200, 50, 50) if hp_percentage < 0.3 else (200, 200, 50) if hp_percentage < 0.6 else (50, 200, 50)
            pygame.draw.rect(self.screen, hp_color, hp_fill_rect)
            
            # Texto de dano
            if slot.damage_text_timer > 0:
                damage_text = f"-{slot.damage_amount}"
                damage_surface = self.font_medium.render(damage_text, True, (255, 100, 100))
                damage_rect = damage_surface.get_rect()
                damage_rect.centerx = rect.centerx
                damage_rect.y = rect.y - 20 - int((2.0 - slot.damage_text_timer) * 20)
                self.screen.blit(damage_surface, damage_rect)
                
    def _draw_hand(self):
        """Desenha as cartas na mão do jogador."""
        for slot in self.card_slots:
            if not slot.card:
                continue
                
            card = slot.card
            rect = slot.get_display_rect()
            
            # Background da carta
            color = (105, 105, 105)  # STONE_MEDIUM
            if slot.is_hovered:
                color = (184, 134, 11)  # GOLD_DARK
            elif self.selected_card == card:
                color = (218, 165, 32)  # GOLD_PRIMARY
                
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (169, 169, 169), rect, 2)  # STONE_LIGHT border
            
            # Nome da carta
            name_text = self.font_small.render(card.name, True, (245, 245, 220))  # PARCHMENT
            name_rect = name_text.get_rect()
            name_rect.centerx = rect.centerx
            name_rect.y = rect.y + 10
            self.screen.blit(name_text, name_rect)
            
            # Custo da carta
            cost_text = f"{card.cost}"
            cost_surface = self.font_medium.render(cost_text, True, (255, 215, 0))  # GOLD_LIGHT
            cost_rect = cost_surface.get_rect()
            cost_rect.x = rect.x + 5
            cost_rect.y = rect.y + 5
            
            # Background do custo
            cost_bg = pygame.Rect(cost_rect.x - 2, cost_rect.y - 2, cost_rect.width + 4, cost_rect.height + 4)
            pygame.draw.ellipse(self.screen, (47, 47, 47), cost_bg)  # STONE_DARK
            self.screen.blit(cost_surface, cost_rect)
            
            # Tipo da carta
            type_text = card.card_type.value
            type_surface = self.font_small.render(type_text, True, (245, 245, 220))  # PARCHMENT
            type_rect = type_surface.get_rect()
            type_rect.centerx = rect.centerx
            type_rect.y = rect.bottom - 20
            self.screen.blit(type_surface, type_rect)
            
    def _draw_player_info(self):
        """Desenha informações do jogador."""
        player = self.combat_engine.player
        
        # Background da info
        info_rect = pygame.Rect(20, self.height - 120, 200, 80)
        pygame.draw.rect(self.screen, (47, 47, 47), info_rect)  # STONE_DARK
        pygame.draw.rect(self.screen, (169, 169, 169), info_rect, 2)  # STONE_LIGHT border
        
        # HP do jogador
        hp_text = f"HP: {player.hp}/{player.max_hp}"
        hp_surface = self.font_medium.render(hp_text, True, (245, 245, 220))  # PARCHMENT
        self.screen.blit(hp_surface, (info_rect.x + 10, info_rect.y + 10))
        
        # Mana do jogador
        mana_text = f"Mana: {player.mana}/{player.max_mana}"
        mana_surface = self.font_medium.render(mana_text, True, (255, 215, 0))  # GOLD_LIGHT
        self.screen.blit(mana_surface, (info_rect.x + 10, info_rect.y + 35))
        
        # Tamanho do deck (simplificado por enquanto)
        deck_size = 20  # Valor fixo para evitar problemas de tipo
        deck_text = f"Deck: {deck_size}"
        deck_surface = self.font_small.render(deck_text, True, (245, 245, 220))  # PARCHMENT
        self.screen.blit(deck_surface, (info_rect.x + 10, info_rect.y + 55))
        
    def _draw_ui_elements(self):
        """Desenha elementos da interface."""
        # Botão de finalizar turno
        end_turn_color = (47, 47, 47)  # STONE_DARK
        if self.state != CombatState.PLAYER_TURN:
            end_turn_color = (60, 60, 60)  # button_disabled_color
            
        pygame.draw.rect(self.screen, end_turn_color, self.end_turn_button)
        pygame.draw.rect(self.screen, (184, 134, 11), self.end_turn_button, 2)  # GOLD_DARK border
        
        end_turn_text = self.font_medium.render("End Turn", True, (245, 245, 220))  # PARCHMENT
        text_rect = end_turn_text.get_rect()
        text_rect.center = self.end_turn_button.center
        self.screen.blit(end_turn_text, text_rect)
        
        # Botão de pausa
        pygame.draw.rect(self.screen, (47, 47, 47), self.pause_button)  # STONE_DARK
        pygame.draw.rect(self.screen, (184, 134, 11), self.pause_button, 2)  # GOLD_DARK border
        
        pause_text = self.font_medium.render("Pause", True, (245, 245, 220))  # PARCHMENT
        text_rect = pause_text.get_rect()
        text_rect.center = self.pause_button.center
        self.screen.blit(pause_text, text_rect)
        
    def _draw_state_overlay(self):
        """Desenha overlay específico do estado atual."""
        if self.state == CombatState.TARGET_SELECTION:
            # Overlay para seleção de alvo
            overlay = pygame.Surface((self.width, self.height))
            overlay.set_alpha(100)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            # Texto de instrução
            instruction = "Select a target for your card"
            text_surface = self.font_large.render(instruction, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.center = (self.width // 2, self.height // 2)
            self.screen.blit(text_surface, text_rect)
            
        elif self.state == CombatState.VICTORY:
            self._draw_victory_screen()
            
        elif self.state == CombatState.DEFEAT:
            self._draw_defeat_screen()
            
        elif self.state == CombatState.PAUSED:
            self._draw_pause_screen()
            
    def _draw_victory_screen(self):
        """Desenha tela de vitória."""
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(150)
        overlay.fill((0, 50, 0))
        self.screen.blit(overlay, (0, 0))
        
        victory_text = self.font_large.render("VICTORY!", True, (100, 255, 100))
        text_rect = victory_text.get_rect()
        text_rect.center = (self.width // 2, self.height // 2)
        self.screen.blit(victory_text, text_rect)
        
    def _draw_defeat_screen(self):
        """Desenha tela de derrota."""
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(150)
        overlay.fill((50, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        defeat_text = self.font_large.render("DEFEAT!", True, (255, 100, 100))
        text_rect = defeat_text.get_rect()
        text_rect.center = (self.width // 2, self.height // 2)
        self.screen.blit(defeat_text, text_rect)
        
    def _draw_pause_screen(self):
        """Desenha tela de pausa."""
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(150)
        overlay.fill((30, 30, 30))
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font_large.render("PAUSED", True, (255, 255, 255))
        text_rect = pause_text.get_rect()
        text_rect.center = (self.width // 2, self.height // 2)
        self.screen.blit(pause_text, text_rect)
        
    def run(self) -> bool:
        """
        Executa a tela de combate.
        
        Returns:
            True se o combate foi concluído, False se foi cancelado
        """
        clock = pygame.time.Clock()
        
        while self.running:
            dt = clock.tick(60) / 1000.0  # Delta time em segundos
            
            # Processar eventos
            for event in pygame.event.get():
                self.handle_event(event)
                
            # Verificar condições de saída
            if self.state in [CombatState.VICTORY, CombatState.DEFEAT]:
                # Aguardar input para sair
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE] or keys[pygame.K_RETURN]:
                    return self.state == CombatState.VICTORY
                    
            # Atualizar
            self.update(dt)
            
            # Renderizar
            self.draw()
            pygame.display.flip()
            
        return False
