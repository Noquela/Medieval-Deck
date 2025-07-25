"""
Main UI system for Medieval Deck.

Manages all screens and handles the main game loop with Pygame.
"""

import pygame
import sys
import logging
from typing import Optional, Dict, Any
from enum import Enum

from ..utils.config import Config
from ..generators.asset_generator import AssetGenerator
from .engine import GameEngine, GamePhase
from .cards import CardManager
from .deck import DeckManager
from .menu_screen import MenuScreen
from .clean_menu_screen import CleanMenuScreen
from .character_selection_screen import CharacterSelectionScreen
from .clean_character_selection_screen import CleanCharacterSelectionScreen
from .cinematic_character_screen import CinematicCharacterSelectionScreen
from .character_screens import CharacterScreenManager
from .stats_screen import StatsScreen
from .story_screen import StoryScreen
from ..ui.combat_screen import CombatScreen
from ..enemies.intelligent_combat import IntelligentCombatEngine
from ..core.turn_engine import Player
from ..gameplay.deck import DeckBuilder

logger = logging.getLogger(__name__)


class UIState(Enum):
    """UI states."""
    MENU = "menu"
    CLEAN_MENU = "clean_menu"
    CHARACTER_SELECTION = "character_selection"
    CLEAN_CHARACTER_SELECTION = "clean_character_selection"
    CINEMATIC_CHARACTER_SELECTION = "cinematic_character_selection"
    CHARACTER_DETAIL = "character_detail"  # Nova tela individual de personagem
    GAME = "game"
    COMBAT = "combat"
    DECK_BUILDER = "deck_builder"
    STATS = "stats"
    STORY = "story"
    SETTINGS = "settings"
    EXIT = "exit"


class GameUI:
    """
    Main UI controller for Medieval Deck.
    
    Manages all screens, handles input, and coordinates the game flow.
    """
    
    def __init__(
        self,
        config: Config,
        game_engine: GameEngine,
        asset_generator: Optional[AssetGenerator] = None
    ):
        """
        Initialize game UI.
        
        Args:
            config: Configuration object
            game_engine: Game engine instance
            asset_generator: Asset generator for AI backgrounds
        """
        self.config = config
        self.game_engine = game_engine
        self.asset_generator = asset_generator
        
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        
        # Create display
        self.screen_width = self.config.ui.window_width
        self.screen_height = self.config.ui.window_height
        
        logger.info(f"Creating display: {self.screen_width}x{self.screen_height}")
        
        if self.config.ui.fullscreen:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
            logger.info("Display created in fullscreen mode")
        else:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            logger.info("Display created in windowed mode")
            
        pygame.display.set_caption("Medieval Deck")
        
        # Clock for frame rate
        self.clock = pygame.time.Clock()
        self.fps = self.config.ui.fps
        
        # Game components
        self.card_manager = CardManager(self.config)
        self.deck_manager = DeckManager(self.card_manager, self.config)
        
        # UI state
        self.current_state = UIState.MENU  # Voltar para o menu original
        self.running = True
        
        # Screens
        self.screens: Dict[UIState, Any] = {}
        self.character_screen_manager = None  # Gerenciador das telas de personagens
        self._initialize_screens()
        
        # Transition effects
        self.transition_alpha = 0
        self.transitioning = False
        
        logger.info("Game UI initialized")
        
        # Initialize the starting screen
        initial_screen = self.screens.get(self.current_state)
        if initial_screen and hasattr(initial_screen, 'enter_screen'):
            logger.info(f"Initializing starting screen: {self.current_state.value}")
            initial_screen.enter_screen()
        
    def _initialize_screens(self) -> None:
        """Initialize all screen objects."""
        try:
            # Menu screens
            self.screens[UIState.MENU] = MenuScreen(
                self.screen,
                self.config,
                self.asset_generator
            )
            
            # Clean menu (new default)
            self.screens[UIState.CLEAN_MENU] = CleanMenuScreen(
                self.screen,
                self.config,
                self.asset_generator
            )
            
            # Character selection screens
            self.screens[UIState.CHARACTER_SELECTION] = CharacterSelectionScreen(
                self.screen,
                self.config,
                self.asset_generator
            )
            
            # Clean character selection (new)
            self.screens[UIState.CLEAN_CHARACTER_SELECTION] = CleanCharacterSelectionScreen(
                self.screen,
                self.config,
                self.asset_generator
            )
            
            # Cinematic character selection screen
            self.screens[UIState.CINEMATIC_CHARACTER_SELECTION] = CinematicCharacterSelectionScreen(
                self.screen,
                self.config,
                self.asset_generator
            )
            
            # Gerenciador de telas individuais de personagens
            self.character_screen_manager = CharacterScreenManager(
                self.screen,
                self.config,
                self.asset_generator
            )
            
            # Initialize combat screen
            self.screens[UIState.COMBAT] = None  # Will be initialized when needed
            
            # Other screens will be initialized when needed
            # self.screens[UIState.STATS] = StatsScreen(...)
            # self.screens[UIState.STORY] = StoryScreen(...)
            
            logger.info("All screens initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize screens: {e}")
            raise
            
    def handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE and self.current_state == UIState.MENU:
                    self.running = False
                    
            # Pass event to current screen
            if self.current_state == UIState.CHARACTER_DETAIL:
                # Tela individual de personagem
                current_character_screen = self.character_screen_manager.get_current_screen()
                if current_character_screen:
                    action = current_character_screen.handle_event(event)
                    if action:
                        self._handle_screen_action(action)
            else:
                # Telas normais
                current_screen = self.screens.get(self.current_state)
                if current_screen and hasattr(current_screen, 'handle_event'):
                    action = current_screen.handle_event(event)
                    
                    if action:
                        self._handle_screen_action(action)
                    
    def _handle_screen_action(self, action: str) -> None:
        """
        Handle actions from screens.
        
        Args:
            action: Action string from screen
        """
        # Verificar se action é uma string válida
        if not action or not isinstance(action, str):
            return
            
        if action == "new_game":
            self._start_new_game()
        elif action == "combat_test":
            self._start_combat_test()
        elif action == "deck_builder":
            self._open_deck_builder()
        elif action == "settings":
            self._open_settings()
        elif action == "quit_game":
            self.running = False
        elif action == "back_to_menu":
            self._transition_to_state(UIState.MENU)
        elif action == "confirm_selection":
            self._confirm_character_selection()
        elif action == "back":
            self._transition_to_state(UIState.MENU)
        elif action == "exit_combat":
            self._transition_to_state(UIState.MENU)
        # Ações da tela cinematográfica
        elif action.startswith("select_"):
            character_id = action.replace("select_", "")
            self._select_cinematic_character(character_id)
        # Novas ações para telas individuais de personagens
        elif action.startswith("show_character_"):
            character_type = action.replace("show_character_", "")
            self._show_character_detail(character_type)
        elif action == "select_character":
            # Selecionar personagem da tela de seleção atual
            if self.current_state == UIState.CHARACTER_SELECTION:
                self._confirm_character_selection()
            elif self.current_state == UIState.CLEAN_CHARACTER_SELECTION:
                self._confirm_clean_character_selection()
            elif self.current_state == UIState.CHARACTER_DETAIL:
                self._select_character_from_detail()
        elif action == "back_to_selection":
            self._transition_to_state(UIState.CHARACTER_SELECTION)
            
    def _select_cinematic_character(self, character_id: str) -> None:
        """
        Seleciona um personagem da tela cinematográfica.
        
        Args:
            character_id: ID do personagem (knight, wizard, assassin)
        """
        logger.info(f"Personagem cinematográfico selecionado: {character_id}")
        
        # Inicializar tela de combate se ainda não foi criada
        if self.screens[UIState.COMBAT] is None:
            logger.info("Combat screen not initialized, creating now...")
            self._initialize_combat_screen(character_id)
        else:
            logger.info("Combat screen already exists")
        
        # Verificar se foi criada com sucesso
        if self.screens[UIState.COMBAT] is not None:
            logger.info("Combat screen ready, transitioning to combat state")
            # Transição para a tela de combate
            self._transition_to_state(UIState.COMBAT)
            logger.info(f"Jogo iniciado com {character_id}!")
        else:
            logger.error("Combat screen creation failed, staying in current state")
            # Não fazer transição se falhou
    
    def _initialize_combat_screen(self, character_id: str) -> None:
        """
        Inicializa a tela de combate com o personagem selecionado.
        
        Args:
            character_id: ID do personagem (knight, wizard, assassin)
        """
        try:
            logger.info(f"Initializing combat screen for character: {character_id}")
            
            # Criar player baseado no personagem selecionado
            player = Player(max_hp=30, max_mana=10)
            logger.info(f"Player created: HP={player.hp}/{player.max_hp}, Mana={player.mana}/{player.max_mana}")
            
            # Inicializar combat engine com player
            combat_engine = IntelligentCombatEngine(
                player=player,
                encounter_type="goblin_patrol"
            )
            logger.info(f"Combat engine created with encounter: goblin_patrol")
            
            # Criar a tela de combate
            self.screens[UIState.COMBAT] = CombatScreen(
                self.screen,
                combat_engine,
                self.asset_generator
            )
            
            logger.info(f"Combat screen initialized successfully for character: {character_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize combat screen: {e}", exc_info=True)
            # Fallback para o menu
            self._transition_to_state(UIState.MENU)
            
    def _show_character_detail(self, character_type: str) -> None:
        """
        Mostra a tela detalhada de um personagem específico.
        
        Args:
            character_type: Tipo do personagem (knight_01, wizard_01, assassin_01)
        """
        logger.info(f"Exibindo detalhes do personagem: {character_type}")
        
        # Criar tela do personagem
        character_screen = self.character_screen_manager.show_character(character_type)
        
        if character_screen:
            self.current_state = UIState.CHARACTER_DETAIL
        else:
            logger.error(f"Falha ao criar tela do personagem: {character_type}")
    
    def _select_character_from_detail(self) -> None:
        """Seleciona o personagem atual da tela de detalhes."""
        current_character_screen = self.character_screen_manager.get_current_screen()
        
        if current_character_screen:
            character_name = current_character_screen.character_data['name']
            character_type = current_character_screen.character_data['type']
            
            logger.info(f"Personagem selecionado: {character_name} ({character_type})")
            
            # TODO: Iniciar jogo com personagem selecionado
            # Por enquanto, volta para o menu
            self._transition_to_state(UIState.MENU)
        else:
            logger.error("Nenhum personagem selecionado")
            
    def _start_new_game(self) -> None:
        """Start a new game - go to character selection."""
        logger.info("Starting new game...")
        self._transition_to_state(UIState.CHARACTER_SELECTION)  # Use the original character selection with backgrounds
        
    def _start_combat_test(self) -> None:
        """Start combat test directly with default character."""
        logger.info("Starting combat test...")
        # Use default knight character for testing
        self._select_cinematic_character("knight")
        
    def _confirm_character_selection(self) -> None:
        """Confirm character selection and start game."""
        if self.current_state == UIState.CHARACTER_SELECTION:
            char_screen = self.screens[UIState.CHARACTER_SELECTION]
            selected_char = char_screen.get_selected_character()
            if selected_char:
                logger.info(f"Character selected: {selected_char}")
                # Iniciar combate com personagem selecionado
                self._select_cinematic_character(selected_char)
                
    def _confirm_clean_character_selection(self) -> None:
        """Confirm character selection from clean screen and start game."""
        if self.current_state == UIState.CLEAN_CHARACTER_SELECTION:
            char_screen = self.screens[UIState.CLEAN_CHARACTER_SELECTION]
            selected_char = char_screen.get_selected_character()
            if selected_char:
                logger.info(f"Character selected from clean screen: {selected_char}")
                # Iniciar combate com personagem selecionado
                self._select_cinematic_character(selected_char)
        
    def _open_deck_builder(self) -> None:
        """Open deck builder."""
        logger.info("Opening deck builder...")
        
        # TODO: Implement deck builder screen
        
    def _open_settings(self) -> None:
        """Open settings screen."""
        logger.info("Opening settings...")
        
        # TODO: Implement settings screen
        
    def _transition_to_state(self, new_state: UIState) -> None:
        """
        Transition to a new UI state.
        
        Args:
            new_state: Target UI state
        """
        if new_state == self.current_state:
            return
            
        logger.debug(f"Transitioning from {self.current_state.value} to {new_state.value}")
        
        # Call exit method on current screen if it exists
        current_screen = self.screens.get(self.current_state)
        if current_screen and hasattr(current_screen, 'exit_screen'):
            current_screen.exit_screen()
            
        self.current_state = new_state
        
        # Call enter method on new screen if it exists
        new_screen = self.screens.get(new_state)
        if new_screen and hasattr(new_screen, 'enter_screen'):
            new_screen.enter_screen()
            
    def _toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        self.config.ui.fullscreen = not self.config.ui.fullscreen
        
        if self.config.ui.fullscreen:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            
        # Reinitialize screens with new display
        self._initialize_screens()
        
        logger.info(f"Fullscreen toggled: {self.config.ui.fullscreen}")
        
    def update(self, dt: float) -> None:
        """
        Update current screen.
        
        Args:
            dt: Delta time in seconds
        """
        # Update current screen
        if self.current_state == UIState.CHARACTER_DETAIL:
            # Atualizar tela individual de personagem
            current_character_screen = self.character_screen_manager.get_current_screen()
            if current_character_screen:
                current_character_screen.update(dt)
        else:
            # Atualizar telas normais
            current_screen = self.screens.get(self.current_state)
            if current_screen and hasattr(current_screen, 'update'):
                current_screen.update(dt)
            
        # Update game engine
        if self.current_state == UIState.GAME:
            # TODO: Update game engine when game screen is implemented
            pass
        elif self.current_state == UIState.COMBAT:
            # Update combat screen
            current_screen = self.screens.get(self.current_state)
            if current_screen and hasattr(current_screen, 'update'):
                current_screen.update(dt)
            
    def draw(self) -> None:
        """Draw current screen."""
        # REMOVIDO: Clear screen - deixar cada tela gerenciar seu próprio background
        # self.screen.fill((20, 20, 30))  # Dark blue-gray background
        
        # Draw current screen
        if self.current_state == UIState.CHARACTER_DETAIL:
            # Desenhar tela individual de personagem
            current_character_screen = self.character_screen_manager.get_current_screen()
            if current_character_screen:
                current_character_screen.draw()
        else:
            # Desenhar telas normais
            current_screen = self.screens.get(self.current_state)
            if current_screen and hasattr(current_screen, 'draw'):
                current_screen.draw()
            else:
                # Fallback: draw placeholder
                self._draw_placeholder()
            
        # Draw debug info if enabled (simplified check)
        # if self.config.debug.get("show_fps", False):
        #     self._draw_debug_info()
            
        # Update display
        pygame.display.flip()
        
    def _draw_placeholder(self) -> None:
        """Draw placeholder for unimplemented screens."""
        font = pygame.font.Font(None, 48)
        text = font.render(f"{self.current_state.value.title()} - Coming Soon!", True, (255, 255, 255))
        rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text, rect)
        
        # Back instruction
        instruction_font = pygame.font.Font(None, 24)
        instruction_text = instruction_font.render("Press ESC to go back", True, (200, 200, 200))
        instruction_rect = instruction_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 60))
        self.screen.blit(instruction_text, instruction_rect)
        
    def _draw_debug_info(self) -> None:
        """Draw debug information."""
        font = pygame.font.Font(None, 24)
        
        # FPS
        fps_text = font.render(f"FPS: {self.clock.get_fps():.1f}", True, (255, 255, 0))
        self.screen.blit(fps_text, (10, 10))
        
        # Current state
        state_text = font.render(f"State: {self.current_state.value}", True, (255, 255, 0))
        self.screen.blit(state_text, (10, 35))
        
        # Memory info if available
        if self.asset_generator:
            try:
                memory_info = self.asset_generator.sdxl_pipeline.get_memory_usage()
                memory_text = font.render(f"VRAM: {memory_info['allocated']:.1f}GB", True, (255, 255, 0))
                self.screen.blit(memory_text, (10, 60))
            except Exception:
                pass
                
    def run(self) -> int:
        """
        Main game loop.
        
        Returns:
            Exit code (0 for success)
        """
        logger.info("Starting main game loop")
        
        try:
            while self.running:
                # Calculate delta time
                dt = self.clock.tick(self.fps) / 1000.0
                
                # Handle events
                self.handle_events()
                
                # Update
                self.update(dt)
                
                # Draw
                self.draw()
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            return 1
            
        finally:
            self._cleanup()
            
        logger.info("Game loop ended")
        return 0
        
    def _cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up resources...")
        
        # Save configuration
        try:
            self.config.save_configs()
        except Exception as e:
            logger.warning(f"Failed to save config: {e}")
            
        # Cleanup pygame
        pygame.quit()
        
        # Cleanup AI pipeline if available
        if self.asset_generator and self.asset_generator.sdxl_pipeline:
            try:
                self.asset_generator.sdxl_pipeline.unload_models()
            except Exception as e:
                logger.warning(f"Failed to cleanup AI pipeline: {e}")
                
        logger.info("Cleanup complete")
