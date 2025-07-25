"""
Game Engine for Medieval Deck.

Core game logic and state management.
"""

import logging
from typing import Optional, List, Dict, Any
from enum import Enum
import pygame
from pathlib import Path

from ..models.card_models import GameState, Player, Card, Deck
from ..utils.config import Config

logger = logging.getLogger(__name__)


class GamePhase(Enum):
    """Game phases."""
    MENU = "menu"
    DECK_BUILDING = "deck_building"
    MATCH_SETUP = "match_setup"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    STATS = "stats"
    STORY = "story"


class GameEngine:
    """
    Main game engine for Medieval Deck.
    
    Manages game state, player actions, and game flow.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize game engine.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.game_state = GameState()
        self.current_phase = GamePhase.MENU
        self.selected_card: Optional[Card] = None
        self.hovered_card: Optional[Card] = None
        
        # Game statistics
        self.stats = {
            "games_played": 0,
            "games_won": 0,
            "cards_played": 0,
            "total_damage_dealt": 0
        }
        
        logger.info("Game Engine initialized")
        
    def start_new_game(self, player_names: List[str]) -> bool:
        """
        Start a new game with given players.
        
        Args:
            player_names: List of player names
            
        Returns:
            True if game started successfully
        """
        try:
            # Reset game state
            self.game_state = GameState()
            
            # Create players
            for name in player_names:
                player = Player(
                    name=name,
                    health=self.config.game.starting_health,
                    max_health=self.config.game.starting_health
                )
                self.game_state.add_player(player)
                
            # Set phase
            self.current_phase = GamePhase.MATCH_SETUP
            
            logger.info(f"New game started with players: {player_names}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start new game: {e}")
            return False
            
    def end_turn(self) -> None:
        """End current player's turn."""
        if self.current_phase != GamePhase.PLAYING:
            return
            
        self.game_state.next_turn()
        
        # Check win condition
        winner = self.game_state.check_win_condition()
        if winner is not None:
            self.current_phase = GamePhase.GAME_OVER
            self.stats["games_played"] += 1
            
        logger.debug(f"Turn ended. Current player: {self.game_state.active_player}")
        
    def play_card(self, card_id: str, player_index: int) -> bool:
        """
        Play a card for a player.
        
        Args:
            card_id: ID of card to play
            player_index: Index of player playing the card
            
        Returns:
            True if card was played successfully
        """
        if self.current_phase != GamePhase.PLAYING:
            return False
            
        if player_index != self.game_state.active_player:
            return False
            
        player = self.game_state.get_current_player()
        if player and player.play_card(card_id):
            self.stats["cards_played"] += 1
            logger.info(f"Player {player.name} played card {card_id}")
            return True
            
        return False
        
    def get_current_player(self) -> Optional[Player]:
        """Get the currently active player."""
        return self.game_state.get_current_player()
        
    def get_game_stats(self) -> Dict[str, Any]:
        """Get current game statistics."""
        return {
            **self.stats,
            "current_turn": self.game_state.turn,
            "current_phase": self.current_phase.value,
            "players": len(self.game_state.players)
        }
        
    def set_phase(self, phase: GamePhase) -> None:
        """Set current game phase."""
        old_phase = self.current_phase
        self.current_phase = phase
        logger.debug(f"Phase changed: {old_phase.value} -> {phase.value}")
        
    def select_card(self, card: Optional[Card]) -> None:
        """Select a card."""
        self.selected_card = card
        
    def hover_card(self, card: Optional[Card]) -> None:
        """Set hovered card."""
        self.hovered_card = card
        
    def is_game_over(self) -> bool:
        """Check if game is over."""
        return self.current_phase == GamePhase.GAME_OVER
        
    def get_winner(self) -> Optional[Player]:
        """Get winning player if game is over."""
        if self.game_state.winner is not None:
            return self.game_state.players[self.game_state.winner]
        return None
