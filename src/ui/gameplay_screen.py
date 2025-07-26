"""
Medieval Deck - Tela de Gameplay Principal

Implementa a tela principal do jogo com funcionalidades básicas:
- Sistema de combate visual
- Gerenciamento de cartas
- Animações 30fps
- Interface de usuário completa
- Sistema de turnos
"""
import logging
import pygame
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pathlib import Path

from ..core.turn_engine import Player, TurnEngine, GameState
from ..gameplay.cards import Card, CardType, Deck
from ..gameplay.gameplay_engine import GameplayEngine

# Adicionar tipos que podem estar faltando
if not hasattr(CardType, 'ATTACK'):
    CardType.ATTACK = "attack"
if not hasattr(CardType, 'DEFENSE'):
    CardType.DEFENSE = "defense"  
if not hasattr(CardType, 'UTILITY'):
    CardType.UTILITY = "utility"
from ..enemies.smart_enemies import SmartEnemy, EnemyType
from ..enemies.intelligent_combat import IntelligentCombatEngine
from ..ui.theme import UITheme, theme
from ..ui.animation import AnimationManager, EasingType
from ..ui.particles import ParticleSystem, ParticleEmitter, ParticleType
from ..ui.helpers import fit_height, fit_width, create_gradient_surface, draw_outlined_text, apply_glow_effect
from ..components.button import Button
from ..generators.asset_generator import AssetGenerator
from ..utils.asset_loader import load_ia_assets
from ..gameplay.animation import animation_manager
from ..utils.sprite_loader import load_character_animations, scale_animation_frames

logger = logging.getLogger(__name__)


class GameplayState(Enum):
    """Estados principais da gameplay."""
    MAIN_MENU = "main_menu"
    CHARACTER_SELECT = "character_select"
    DECK_BUILD = "deck_build"
    COMBAT = "combat"
    VICTORY = "victory"
    DEFEAT = "defeat"
    PAUSE = "pause"
    SETTINGS = "settings"


class GameplayScreen:
    """
    Tela principal de gameplay com sistema completo de jogo.
    
    Funcionalidades:
    - Sistema de combate com animações 30fps
    - Gerenciamento de cartas e deck
    - Interface de usuário responsiva
    - Sistema de turnos automático
    - Efeitos visuais e partículas
    - Navegação entre telas
    """
    
    def __init__(self, screen: pygame.Surface):
        """
        Inicializa a tela de gameplay.
        
        Args:
            screen: Surface principal do pygame
        """
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.clock = pygame.time.Clock()
        
        # Estado do jogo
        self.state = GameplayState.MAIN_MENU
        self.running = True
        self.last_frame_time = 0
        
        # Componentes de jogo
        self.player: Optional[Player] = None
        self.current_deck: Optional[Deck] = None
        self.combat_engine: Optional[IntelligentCombatEngine] = None
        self.gameplay_engine: Optional[GameplayEngine] = None
        
        # Assets e recursos
        self.assets = {}
        self.fonts = {}
        self.sounds = {}
        
        # Inicialização
        self._initialize_components()
        self._load_assets()
        self._setup_ui()
        
        logger.info("GameplayScreen inicializada")
        
    def _initialize_components(self):
        """Inicializa os componentes básicos do jogo."""
        # Sistema de partículas
        self.particle_system = ParticleSystem()
        
        # Carregar fontes
        pygame.font.init()
        self.fonts = {
            "title": pygame.font.Font(None, 48),
            "subtitle": pygame.font.Font(None, 32),
            "text": pygame.font.Font(None, 24),
            "small": pygame.font.Font(None, 18)
        }
        
        # Inicializar player padrão
        self.player = Player(
            max_hp=100,
            max_mana=50
        )
        # Adicionar propriedades adicionais manualmente
        self.player.name = "Hero"
        self.player.character_class = "Knight"
        
        logger.info("Componentes básicos inicializados")
        
    def _load_assets(self):
        """Carrega todos os assets necessários."""
        try:
            # Carregar assets IA
            self.assets.update(load_ia_assets("assets/ia"))
            
            # Carregar backgrounds regenerados
            bg_paths = [
                "assets/generated/character_selection_bg.png",
                "assets/generated/deck_selection_bg.png", 
                "assets/generated/main_menu_bg.png",
                "assets/generated/settings_bg.png"
            ]
            
            for bg_path in bg_paths:
                if Path(bg_path).exists():
                    bg_name = Path(bg_path).stem
                    self.assets[bg_name] = pygame.image.load(bg_path).convert_alpha()
                    logger.info(f"Background carregado: {bg_name}")
            
            # Carregar sprites de personagens
            sprite_paths = Path("assets/generated").glob("*_sprite_transparent.png")
            for sprite_path in sprite_paths:
                sprite_name = sprite_path.stem.replace("_transparent", "")
                self.assets[sprite_name] = pygame.image.load(sprite_path).convert_alpha()
                logger.info(f"Sprite carregado: {sprite_name}")
            
            # Carregar animações
            self._load_animations()
            
            logger.info(f"Assets carregados: {len(self.assets)} items")
            
        except Exception as e:
            logger.error(f"Erro ao carregar assets: {e}")
            
    def _load_animations(self):
        """Carrega sprite sheets de animação."""
        try:
            animations_dir = Path("assets/generated/animations")
            if animations_dir.exists():
                sprite_sheets = list(animations_dir.glob("*_sheet.png"))
                logger.info(f"Encontradas {len(sprite_sheets)} animações")
                
                for sheet_path in sprite_sheets:
                    # Extrair informações do nome do arquivo
                    # Formato: character_animation_sheet.png
                    name_parts = sheet_path.stem.replace("_sheet", "").split("_")
                    if len(name_parts) >= 2:
                        character = name_parts[0]
                        animation = name_parts[1]
                        
                        # Carregar sprite sheet
                        sheet_image = pygame.image.load(sheet_path).convert_alpha()
                        
                        # Extrair frames individuais (assumindo 8 frames por sheet)
                        frame_width = sheet_image.get_width() // 8
                        frame_height = sheet_image.get_height()
                        
                        frames = []
                        for i in range(8):
                            frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                            frame = sheet_image.subsurface(frame_rect).copy()
                            frames.append(frame)
                        
                        # Adicionar ao animation manager
                        animation_manager.add_animation(
                            entity_id=character,
                            action=animation,
                            frames=frames,
                            fps=30,
                            loop=(animation == "idle")
                        )
                        
                        logger.info(f"Animação carregada: {character}.{animation} ({len(frames)} frames)")
            
        except Exception as e:
            logger.error(f"Erro ao carregar animações: {e}")
            
    def _setup_ui(self):
        """Configura a interface de usuário."""
        self.ui_elements = {}
        
        # Botões do menu principal
        button_width = 200
        button_height = 50
        button_x = self.width // 2 - button_width // 2
        start_y = self.height // 2
        
        self.ui_elements["main_menu"] = {
            "play_button": Button(
                x=button_x, y=start_y,
                width=button_width, height=button_height,
                text="Jogar", on_click=self._start_character_select,
                style="medieval"
            ),
            "deck_button": Button(
                x=button_x, y=start_y + 70,
                width=button_width, height=button_height,
                text="Construir Deck", on_click=self._start_deck_build,
                style="medieval"
            ),
            "settings_button": Button(
                x=button_x, y=start_y + 140,
                width=button_width, height=button_height,
                text="Configurações", on_click=self._show_settings,
                style="medieval"
            ),
            "quit_button": Button(
                x=button_x, y=start_y + 210,
                width=button_width, height=button_height,
                text="Sair", on_click=self._quit_game,
                style="medieval"
            )
        }
        
        # Botões de seleção de personagem
        char_button_width = 120
        char_button_height = 160
        chars_per_row = 4
        start_x = (self.width - (chars_per_row * char_button_width + (chars_per_row - 1) * 20)) // 2
        char_y = self.height // 2 - 50
        
        characters = ["knight", "wizard", "rogue", "archer"]
        self.ui_elements["character_select"] = {}
        
        for i, char in enumerate(characters):
            x = start_x + i * (char_button_width + 20)
            self.ui_elements["character_select"][f"{char}_button"] = Button(
                x=x, y=char_y,
                width=char_button_width, height=char_button_height,
                text=char.title(), on_click=lambda c=char: self._select_character(c),
                style="character_card"
            )
        
        # Botão de voltar universal
        self.ui_elements["back_button"] = Button(
            x=50, y=50,
            width=100, height=40,
            text="Voltar", on_click=self._go_back,
            style="secondary"
        )
        
        logger.info("Interface de usuário configurada")
        
    def _start_character_select(self):
        """Inicia a seleção de personagem."""
        self.state = GameplayState.CHARACTER_SELECT
        logger.info("Mudando para seleção de personagem")
        
    def _start_deck_build(self):
        """Inicia a construção de deck."""
        self.state = GameplayState.DECK_BUILD
        logger.info("Mudando para construção de deck")
        
    def _show_settings(self):
        """Mostra as configurações."""
        self.state = GameplayState.SETTINGS
        logger.info("Mudando para configurações")
        
    def _quit_game(self):
        """Sai do jogo."""
        self.running = False
        logger.info("Saindo do jogo")
        
    def _select_character(self, character: str):
        """Seleciona um personagem e inicia o combate."""
        # Atualizar player com personagem selecionado
        self.player.character_class = character.title()
        
        # Criar deck padrão se não existir
        if not self.current_deck:
            self.current_deck = self._create_default_deck()
            
        # Inicializar combate
        self._start_combat()
        
        logger.info(f"Personagem selecionado: {character}")
        
    def _create_default_deck(self) -> Deck:
        """Cria um deck padrão para teste."""
        cards = []
        
        # Cartas básicas de ataque
        for i in range(8):
            cards.append(Card(
                card_id=f"golpe_{i}",
                name="Golpe",
                cost=1,
                card_type=CardType.ATTACK,
                description="Causa 5 de dano"
            ))
        
        # Cartas de defesa
        for i in range(4):
            cards.append(Card(
                card_id=f"bloquear_{i}",
                name="Bloquear",
                cost=1,
                card_type=CardType.DEFENSE,
                description="Ganha 3 de escudo"
            ))
        
        # Cartas especiais
        for i in range(3):
            cards.append(Card(
                card_id=f"cura_{i}",
                name="Cura",
                cost=2,
                card_type=CardType.UTILITY,
                description="Recupera 8 de vida"
            ))
        
        return Deck(cards)
        
    def _start_combat(self):
        """Inicia o sistema de combate."""
        try:
            # Criar inimigos
            enemies = [
                SmartEnemy(
                    name="Goblin Scout",
                    max_hp=30,
                    attack=5,
                    defense=2,
                    enemy_type=EnemyType.GOBLIN
                ),
                SmartEnemy(
                    name="Orc Warrior",
                    max_hp=50,
                    attack=8,
                    defense=4,
                    enemy_type=EnemyType.ORC
                )
            ]
            
            # Inicializar combat engine
            self.combat_engine = IntelligentCombatEngine(
                player=self.player,
                enemies=enemies
            )
            
            # Inicializar gameplay engine
            self.gameplay_engine = GameplayEngine(
                player=self.player,
                deck=self.current_deck
            )
            
            # Inicializar animações de combate
            self._initialize_combat_animations()
            
            # Mudar para estado de combate
            self.state = GameplayState.COMBAT
            
            logger.info("Combate iniciado")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar combate: {e}")
            
    def _initialize_combat_animations(self):
        """Inicializa animações para o combate atual."""
        try:
            # Inicializar animação do jogador
            player_char = self.player.character_class.lower()
            animation_manager.play_animation(player_char, "idle")
            
            # Inicializar animações dos inimigos
            if self.combat_engine:
                for i, enemy in enumerate(self.combat_engine.enemies):
                    enemy_type = enemy.enemy_type.name.lower()
                    unique_id = f"{enemy_type}_{i}"
                    
                    # Copiar animações base para ID único
                    if enemy_type in animation_manager.animations:
                        for action, animation in animation_manager.animations[enemy_type].items():
                            animation_manager.add_animation(
                                entity_id=unique_id,
                                action=action,
                                frames=animation.frames.copy(),
                                fps=animation.fps,
                                loop=animation.loop
                            )
                    
                    # Iniciar animação idle
                    animation_manager.play_animation(unique_id, "idle")
                    
            logger.info("Animações de combate inicializadas")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar animações: {e}")
            
    def _go_back(self):
        """Volta para o estado anterior."""
        if self.state == GameplayState.CHARACTER_SELECT:
            self.state = GameplayState.MAIN_MENU
        elif self.state == GameplayState.DECK_BUILD:
            self.state = GameplayState.MAIN_MENU
        elif self.state == GameplayState.SETTINGS:
            self.state = GameplayState.MAIN_MENU
        elif self.state == GameplayState.COMBAT:
            self.state = GameplayState.CHARACTER_SELECT
        else:
            self.state = GameplayState.MAIN_MENU
            
        logger.info(f"Voltando para: {self.state}")
        
    def update(self, dt: float):
        """
        Atualiza todos os componentes da gameplay.
        
        Args:
            dt: Delta time em segundos
        """
        # Atualizar sistema de animações
        animation_manager.update(dt)
        
        # Atualizar sistema de partículas
        self.particle_system.update(dt)
        
        # Atualizar botões relevantes ao estado atual
        if self.state == GameplayState.MAIN_MENU:
            for button in self.ui_elements["main_menu"].values():
                button.update(dt)
                
        elif self.state == GameplayState.CHARACTER_SELECT:
            for button in self.ui_elements["character_select"].values():
                button.update(dt)
            self.ui_elements["back_button"].update(dt)
            
        elif self.state == GameplayState.COMBAT:
            if self.combat_engine:
                # Atualizar engine de combate
                self.combat_engine.update(dt)
                
                # Verificar fim de combate
                if self.combat_engine.is_game_over():
                    if self.combat_engine.is_victory():
                        self.state = GameplayState.VICTORY
                    else:
                        self.state = GameplayState.DEFEAT
                        
            if self.gameplay_engine:
                self.gameplay_engine.update(dt)
        
        # Atualizar engines de jogo
        if self.gameplay_engine:
            self.gameplay_engine.update(dt)
            
    def handle_event(self, event: pygame.event.Event):
        """
        Processa eventos da gameplay.
        
        Args:
            event: Evento do pygame
        """
        if event.type == pygame.QUIT:
            self.running = False
            return
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == GameplayState.COMBAT:
                    self.state = GameplayState.PAUSE
                else:
                    self._go_back()
                return
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_mouse_click(event.pos)
            
    def _handle_mouse_click(self, pos: Tuple[int, int]):
        """Processa cliques do mouse."""
        if self.state == GameplayState.MAIN_MENU:
            for button in self.ui_elements["main_menu"].values():
                if button.rect.collidepoint(pos):
                    button.on_click()
                    
        elif self.state == GameplayState.CHARACTER_SELECT:
            for button in self.ui_elements["character_select"].values():
                if button.rect.collidepoint(pos):
                    button.on_click()
            if self.ui_elements["back_button"].rect.collidepoint(pos):
                self.ui_elements["back_button"].on_click()
                
        elif self.state == GameplayState.COMBAT:
            # Implementar cliques de combate aqui
            pass
            
    def draw(self):
        """Desenha toda a interface de gameplay."""
        # Limpar tela
        self.screen.fill((20, 15, 30))
        
        # Desenhar baseado no estado atual
        if self.state == GameplayState.MAIN_MENU:
            self._draw_main_menu()
        elif self.state == GameplayState.CHARACTER_SELECT:
            self._draw_character_select()
        elif self.state == GameplayState.DECK_BUILD:
            self._draw_deck_build()
        elif self.state == GameplayState.COMBAT:
            self._draw_combat()
        elif self.state == GameplayState.VICTORY:
            self._draw_victory()
        elif self.state == GameplayState.DEFEAT:
            self._draw_defeat()
        elif self.state == GameplayState.SETTINGS:
            self._draw_settings()
            
        # Desenhar partículas
        # self.particle_system.draw(self.screen)  # Temporarily disabled
        
    def _draw_main_menu(self):
        """Desenha o menu principal."""
        # Background
        if "main_menu_bg" in self.assets:
            bg = pygame.transform.scale(self.assets["main_menu_bg"], (self.width, self.height))
            self.screen.blit(bg, (0, 0))
        
        # Título
        title_text = self.fonts["title"].render("Medieval Deck", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(self.width // 2, 150))
        self.screen.blit(title_text, title_rect)
        
        # Botões
        for button in self.ui_elements["main_menu"].values():
            button.draw(self.screen)
            
    def _draw_character_select(self):
        """Desenha a seleção de personagem."""
        # Background
        if "character_selection_bg" in self.assets:
            bg = pygame.transform.scale(self.assets["character_selection_bg"], (self.width, self.height))
            self.screen.blit(bg, (0, 0))
        
        # Título
        title_text = self.fonts["subtitle"].render("Escolha seu Personagem", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Botões de personagem
        for button_name, button in self.ui_elements["character_select"].items():
            button.draw(self.screen)
            
            # Desenhar sprite do personagem no botão
            char_name = button_name.replace("_button", "")
            sprite_key = f"{char_name}_sprite"
            if sprite_key in self.assets:
                sprite = self.assets[sprite_key]
                # Escalar sprite para caber no botão
                scaled_sprite = pygame.transform.scale(sprite, (100, 140))
                sprite_rect = scaled_sprite.get_rect(center=button.rect.center)
                sprite_rect.y += 10  # Ajustar posição
                self.screen.blit(scaled_sprite, sprite_rect)
        
        # Botão voltar
        self.ui_elements["back_button"].draw(self.screen)
        
    def _draw_deck_build(self):
        """Desenha a construção de deck."""
        # Background
        if "deck_selection_bg" in self.assets:
            bg = pygame.transform.scale(self.assets["deck_selection_bg"], (self.width, self.height))
            self.screen.blit(bg, (0, 0))
        
        # Título
        title_text = self.fonts["subtitle"].render("Construir Deck", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Placeholder para interface de deck
        placeholder_text = self.fonts["text"].render("Interface de construção de deck em desenvolvimento", True, (200, 200, 200))
        placeholder_rect = placeholder_text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(placeholder_text, placeholder_rect)
        
        # Botão voltar
        self.ui_elements["back_button"].draw(self.screen)
        
    def _draw_combat(self):
        """Desenha a tela de combate."""
        # Background de combate
        self.screen.fill((40, 30, 20))
        
        # Zona de inimigos (topo)
        enemy_zone = pygame.Rect(50, 30, self.width - 100, 300)
        enemy_overlay = pygame.Surface(enemy_zone.size, pygame.SRCALPHA)
        enemy_overlay.fill((80, 40, 40, 120))
        self.screen.blit(enemy_overlay, enemy_zone.topleft)
        
        # Desenhar inimigos com animações
        if self.combat_engine and self.combat_engine.enemies:
            enemies = self.combat_engine.enemies
            col_width = enemy_zone.width // len(enemies)
            
            for i, enemy in enumerate(enemies):
                if enemy.hp > 0:  # Apenas inimigos vivos
                    # Animação do inimigo
                    enemy_type = enemy.enemy_type.name.lower()
                    unique_id = f"{enemy_type}_{i}"
                    current_frame = animation_manager.get_current_frame(unique_id)
                    
                    if current_frame:
                        # Posicionar sprite
                        pos_x = enemy_zone.left + col_width // 2 - current_frame.get_width() // 2 + i * col_width
                        pos_y = enemy_zone.bottom - current_frame.get_height()
                        sprite_rect = self.screen.blit(current_frame, (pos_x, pos_y))
                        
                        # Barra de vida
                        bar_width = current_frame.get_width()
                        bar_rect = pygame.Rect(pos_x, pos_y - 15, bar_width, 8)
                        pygame.draw.rect(self.screen, (60, 0, 0), bar_rect)
                        
                        hp_ratio = enemy.hp / enemy.max_hp
                        hp_width = int(bar_width * hp_ratio)
                        hp_rect = pygame.Rect(pos_x, pos_y - 15, hp_width, 8)
                        
                        # Cor da barra baseada no HP
                        if hp_ratio > 0.6:
                            hp_color = (0, 200, 0)
                        elif hp_ratio > 0.3:
                            hp_color = (255, 255, 0)
                        else:
                            hp_color = (200, 0, 0)
                            
                        pygame.draw.rect(self.screen, hp_color, hp_rect)
        
        # Sprite do jogador (centro-baixo)
        player_char = self.player.character_class.lower()
        player_frame = animation_manager.get_current_frame(player_char)
        
        if player_frame:
            player_rect = player_frame.get_rect(midbottom=(self.width // 2, self.height - 250))
            self.screen.blit(player_frame, player_rect)
        
        # Zona da mão do jogador (base)
        hand_zone = pygame.Rect(50, self.height - 220, self.width - 100, 190)
        hand_overlay = pygame.Surface(hand_zone.size, pygame.SRCALPHA)
        hand_overlay.fill((40, 40, 80, 120))
        self.screen.blit(hand_overlay, hand_zone.topleft)
        
        # Placeholder para cartas na mão
        for i in range(5):
            slot_width = hand_zone.width // 5
            slot_x = hand_zone.left + i * slot_width + 10
            slot_y = hand_zone.top + 10
            slot_rect = pygame.Rect(slot_x, slot_y, slot_width - 20, hand_zone.height - 20)
            
            pygame.draw.rect(self.screen, (60, 60, 90), slot_rect)
            pygame.draw.rect(self.screen, (100, 100, 130), slot_rect, 2)
        
        # Interface de combate
        self._draw_combat_ui()
        
    def _draw_combat_ui(self):
        """Desenha a interface de combate."""
        # Painel de status do jogador
        panel_rect = pygame.Rect(50, self.height - 80, 300, 60)
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surface.fill((40, 40, 60, 200))
        
        # HP Bar
        hp_width = 120
        hp_height = 12
        hp_x = 10
        hp_y = 15
        
        hp_bg = pygame.Rect(hp_x, hp_y, hp_width, hp_height)
        pygame.draw.rect(panel_surface, (60, 0, 0), hp_bg)
        
        hp_ratio = self.player.hp / self.player.max_hp
        hp_fill_width = int(hp_width * hp_ratio)
        hp_fill = pygame.Rect(hp_x, hp_y, hp_fill_width, hp_height)
        pygame.draw.rect(panel_surface, (200, 50, 50), hp_fill)
        
        # Texto HP
        hp_text = self.fonts["small"].render(f"HP: {self.player.hp}/{self.player.max_hp}", True, (255, 255, 255))
        panel_surface.blit(hp_text, (hp_x, hp_y - 15))
        
        # Mana Bar
        mana_x = 150
        mana_bg = pygame.Rect(mana_x, hp_y, hp_width, hp_height)
        pygame.draw.rect(panel_surface, (0, 0, 60), mana_bg)
        
        mana_ratio = self.player.mana / self.player.max_mana
        mana_fill_width = int(hp_width * mana_ratio)
        mana_fill = pygame.Rect(mana_x, hp_y, mana_fill_width, hp_height)
        pygame.draw.rect(panel_surface, (50, 50, 200), mana_fill)
        
        mana_text = self.fonts["small"].render(f"Mana: {self.player.mana}/{self.player.max_mana}", True, (255, 255, 255))
        panel_surface.blit(mana_text, (mana_x, hp_y - 15))
        
        self.screen.blit(panel_surface, panel_rect.topleft)
        
        # Botão End Turn
        end_turn_button = pygame.Rect(self.width - 150, self.height - 280, 120, 40)
        pygame.draw.rect(self.screen, (100, 50, 150), end_turn_button)
        pygame.draw.rect(self.screen, (150, 100, 200), end_turn_button, 2)
        
        end_turn_text = self.fonts["text"].render("End Turn", True, (255, 255, 255))
        text_rect = end_turn_text.get_rect(center=end_turn_button.center)
        self.screen.blit(end_turn_text, text_rect)
        
    def _draw_victory(self):
        """Desenha a tela de vitória."""
        # Overlay escuro
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Texto de vitória
        victory_text = self.fonts["title"].render("VITÓRIA!", True, (255, 215, 0))
        victory_rect = victory_text.get_rect(center=(self.width // 2, self.height // 2 - 50))
        self.screen.blit(victory_text, victory_rect)
        
        continue_text = self.fonts["text"].render("Pressione ESC para continuar", True, (255, 255, 255))
        continue_rect = continue_text.get_rect(center=(self.width // 2, self.height // 2 + 50))
        self.screen.blit(continue_text, continue_rect)
        
    def _draw_defeat(self):
        """Desenha a tela de derrota."""
        # Overlay escuro
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Texto de derrota
        defeat_text = self.fonts["title"].render("DERROTA", True, (200, 50, 50))
        defeat_rect = defeat_text.get_rect(center=(self.width // 2, self.height // 2 - 50))
        self.screen.blit(defeat_text, defeat_rect)
        
        continue_text = self.fonts["text"].render("Pressione ESC para continuar", True, (255, 255, 255))
        continue_rect = continue_text.get_rect(center=(self.width // 2, self.height // 2 + 50))
        self.screen.blit(continue_text, continue_rect)
        
    def _draw_settings(self):
        """Desenha a tela de configurações."""
        # Background
        if "settings_bg" in self.assets:
            bg = pygame.transform.scale(self.assets["settings_bg"], (self.width, self.height))
            self.screen.blit(bg, (0, 0))
        
        # Título
        title_text = self.fonts["subtitle"].render("Configurações", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Placeholder para configurações
        placeholder_text = self.fonts["text"].render("Interface de configurações em desenvolvimento", True, (200, 200, 200))
        placeholder_rect = placeholder_text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(placeholder_text, placeholder_rect)
        
        # Botão voltar
        self.ui_elements["back_button"].draw(self.screen)
        
    def run(self):
        """Loop principal da gameplay."""
        while self.running:
            # Calcular delta time
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_frame_time) / 1000.0
            self.last_frame_time = current_time
            
            # Processar eventos
            for event in pygame.event.get():
                self.handle_event(event)
            
            # Atualizar
            self.update(dt)
            
            # Desenhar
            self.draw()
            
            # Atualizar display
            pygame.display.flip()
            self.clock.tick(60)
            
        return True
