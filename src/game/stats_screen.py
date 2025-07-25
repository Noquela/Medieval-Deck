"""
Statistics Screen for Medieval Deck.

Displays detailed card and game statistics with smooth animations.
"""

import pygame
import math
from typing import Dict, Any, List, Tuple, Optional
import logging

from ..utils.config import Config
from ..game.cards import CardManager
from ..game.deck import DeckManager

logger = logging.getLogger(__name__)


class StatsScreen:
    """
    Statistics screen with detailed card and game information.
    
    Features:
    - Animated panel transitions
    - Rounded rectangles for modern look
    - Card statistics and analysis
    - Smooth slide animations
    """
    
    def __init__(self, screen: pygame.Surface, config: Config, card_manager: CardManager, deck_manager: DeckManager):
        """
        Initialize stats screen.
        
        Args:
            screen: Pygame screen surface
            config: Configuration object
            card_manager: Card manager instance
            deck_manager: Deck manager instance
        """
        self.screen = screen
        self.config = config
        self.card_manager = card_manager
        self.deck_manager = deck_manager
        
        # Screen dimensions
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Panel layout
        self.panel_width = 400
        self.panel_height = 500
        self.panel_x = self.width - self.panel_width - 50
        self.panel_y = (self.height - self.panel_height) // 2
        
        # Animation state
        self.panel_offset = self.panel_width  # Start off-screen
        self.target_offset = 0
        self.animation_speed = 8.0
        
        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.header_font = pygame.font.Font(None, 36)
        self.body_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        
        # Colors
        self.bg_color = tuple(self.config.ui.theme["background_color"])
        self.panel_color = (40, 40, 50, 200)  # Semi-transparent
        self.primary_color = tuple(self.config.ui.theme["primary_color"])
        self.text_color = tuple(self.config.ui.theme["text_color"])
        self.accent_color = tuple(self.config.ui.theme["accent_color"])
        self.secondary_color = tuple(self.config.ui.theme["secondary_color"])
        
        # Back button
        self.back_button = pygame.Rect(50, 50, 100, 40)
        
        # Statistics data
        self.stats_data = self._collect_statistics()
        
        logger.info("Stats screen initialized")
        
    def _collect_statistics(self) -> Dict[str, Any]:
        """Collect all statistics data."""
        # Card collection stats
        collection_stats = self.card_manager.get_collection_stats()
        
        # Deck stats
        all_decks = self.deck_manager.get_all_decks()
        deck_stats = {}
        
        for deck_id, deck in all_decks.items():
            deck_stats[deck_id] = self.deck_manager.get_deck_stats(deck)
            
        # Game stats (placeholder - would come from saved game data)
        game_stats = {
            "games_played": 15,
            "games_won": 9,
            "win_rate": 60.0,
            "total_turns": 243,
            "average_game_length": 16.2,
            "favorite_card_type": "creature",
            "most_played_card": "Valiant Knight",
            "total_damage_dealt": 1847,
            "total_cards_played": 312
        }
        
        return {
            "collection": collection_stats,
            "decks": deck_stats,
            "game": game_stats
        }
        
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handle input events.
        
        Args:
            event: Pygame event
            
        Returns:
            Action string if back button clicked, None otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.back_button.collidepoint(event.pos):
                    return "back"
                    
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
                
        return None
        
    def update(self, dt: float) -> None:
        """
        Update animations.
        
        Args:
            dt: Delta time in seconds
        """
        # Animate panel slide-in
        offset_diff = self.target_offset - self.panel_offset
        self.panel_offset += offset_diff * self.animation_speed * dt
        
        # Clamp to target
        if abs(offset_diff) < 1.0:
            self.panel_offset = self.target_offset
            
    def enter_screen(self) -> None:
        """Called when entering the screen."""
        self.panel_offset = self.panel_width
        self.target_offset = 0
        
    def exit_screen(self) -> None:
        """Called when exiting the screen."""
        self.target_offset = self.panel_width
        
    def _draw_rounded_rect(self, surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int, int], radius: int = 10) -> None:
        """
        Draw a rounded rectangle with alpha.
        
        Args:
            surface: Surface to draw on
            rect: Rectangle dimensions
            color: RGBA color
            radius: Corner radius
        """
        # Create a temporary surface with alpha
        temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Draw rounded rectangle using circles and rectangles
        pygame.draw.rect(temp_surface, color, (radius, 0, rect.width - 2 * radius, rect.height))
        pygame.draw.rect(temp_surface, color, (0, radius, rect.width, rect.height - 2 * radius))
        
        # Draw corner circles
        pygame.draw.circle(temp_surface, color, (radius, radius), radius)
        pygame.draw.circle(temp_surface, color, (rect.width - radius, radius), radius)
        pygame.draw.circle(temp_surface, color, (radius, rect.height - radius), radius)
        pygame.draw.circle(temp_surface, color, (rect.width - radius, rect.height - radius), radius)
        
        # Blit to main surface
        surface.blit(temp_surface, rect.topleft)
        
    def _draw_stat_bar(self, surface: pygame.Surface, x: int, y: int, width: int, value: float, max_value: float, color: Tuple[int, int, int]) -> None:
        """
        Draw a statistical bar chart.
        
        Args:
            surface: Surface to draw on
            x, y: Position
            width: Bar width
            value: Current value
            max_value: Maximum value
            color: Bar color
        """
        bar_height = 20
        
        # Background bar
        bg_rect = pygame.Rect(x, y, width, bar_height)
        pygame.draw.rect(surface, (60, 60, 70), bg_rect)
        pygame.draw.rect(surface, self.accent_color, bg_rect, 1)
        
        # Value bar
        if max_value > 0:
            fill_width = int((value / max_value) * width)
            fill_rect = pygame.Rect(x, y, fill_width, bar_height)
            pygame.draw.rect(surface, color, fill_rect)
            
    def draw(self) -> None:
        """Draw the statistics screen."""
        # Clear screen
        self.screen.fill(self.bg_color)
        
        # Draw title
        title_text = self.title_font.render("Statistics", True, self.accent_color)
        title_rect = title_text.get_rect(center=(self.width // 2, 60))
        self.screen.blit(title_text, title_rect)
        
        # Draw back button
        pygame.draw.rect(self.screen, self.primary_color, self.back_button)
        pygame.draw.rect(self.screen, self.accent_color, self.back_button, 2)
        
        back_text = self.body_font.render("Back", True, self.text_color)
        back_rect = back_text.get_rect(center=self.back_button.center)
        self.screen.blit(back_text, back_rect)
        
        # Draw main statistics panel with slide animation
        panel_rect = pygame.Rect(
            self.panel_x + self.panel_offset,
            self.panel_y,
            self.panel_width,
            self.panel_height
        )
        
        # Only draw panel if visible
        if panel_rect.right > 0:
            self._draw_rounded_rect(self.screen, panel_rect, self.panel_color, 15)
            
            # Panel content
            content_x = panel_rect.x + 20
            content_y = panel_rect.y + 20
            content_width = panel_rect.width - 40
            
            y_offset = 0
            
            # Collection Statistics
            header_text = self.header_font.render("Collection", True, self.accent_color)
            self.screen.blit(header_text, (content_x, content_y + y_offset))
            y_offset += 40
            
            collection = self.stats_data["collection"]
            
            # Total cards
            total_text = self.body_font.render(f"Total Cards: {collection['total_cards']}", True, self.text_color)
            self.screen.blit(total_text, (content_x, content_y + y_offset))
            y_offset += 25
            
            # Cards with backgrounds
            bg_text = self.body_font.render(f"With Backgrounds: {collection['with_backgrounds']}", True, self.text_color)
            self.screen.blit(bg_text, (content_x, content_y + y_offset))
            y_offset += 35
            
            # Card type distribution
            type_header = self.body_font.render("By Type:", True, self.secondary_color)
            self.screen.blit(type_header, (content_x, content_y + y_offset))
            y_offset += 25
            
            max_type_count = max(collection["by_type"].values()) if collection["by_type"] else 1
            
            for card_type, count in collection["by_type"].items():
                # Type name and count
                type_text = self.small_font.render(f"{card_type.title()}: {count}", True, self.text_color)
                self.screen.blit(type_text, (content_x + 10, content_y + y_offset))
                
                # Bar chart
                self._draw_stat_bar(
                    self.screen,
                    content_x + 120,
                    content_y + y_offset,
                    150,
                    count,
                    max_type_count,
                    self.primary_color
                )
                
                y_offset += 25
                
            y_offset += 20
            
            # Game Statistics
            header_text = self.header_font.render("Game Stats", True, self.accent_color)
            self.screen.blit(header_text, (content_x, content_y + y_offset))
            y_offset += 40
            
            game_stats = self.stats_data["game"]
            
            # Games played and won
            games_text = self.body_font.render(f"Games Played: {game_stats['games_played']}", True, self.text_color)
            self.screen.blit(games_text, (content_x, content_y + y_offset))
            y_offset += 25
            
            won_text = self.body_font.render(f"Games Won: {game_stats['games_won']}", True, self.text_color)
            self.screen.blit(won_text, (content_x, content_y + y_offset))
            y_offset += 25
            
            # Win rate with bar
            winrate_text = self.body_font.render(f"Win Rate: {game_stats['win_rate']:.1f}%", True, self.text_color)
            self.screen.blit(winrate_text, (content_x, content_y + y_offset))
            
            self._draw_stat_bar(
                self.screen,
                content_x + 150,
                content_y + y_offset + 2,
                120,
                game_stats['win_rate'],
                100.0,
                (50, 200, 50)  # Green color for win rate
            )
            
            y_offset += 35
            
            # Additional stats
            avg_text = self.small_font.render(f"Avg Game Length: {game_stats['average_game_length']:.1f} turns", True, self.text_color)
            self.screen.blit(avg_text, (content_x, content_y + y_offset))
            y_offset += 20
            
            damage_text = self.small_font.render(f"Total Damage: {game_stats['total_damage_dealt']}", True, self.text_color)
            self.screen.blit(damage_text, (content_x, content_y + y_offset))
            y_offset += 20
            
            cards_played_text = self.small_font.render(f"Cards Played: {game_stats['total_cards_played']}", True, self.text_color)
            self.screen.blit(cards_played_text, (content_x, content_y + y_offset))
            
        # Draw left side summary
        summary_x = 100
        summary_y = 150
        
        # Quick stats boxes
        quick_stats = [
            ("Collection", f"{self.stats_data['collection']['total_cards']} cards"),
            ("Win Rate", f"{self.stats_data['game']['win_rate']:.1f}%"),
            ("Games", f"{self.stats_data['game']['games_played']} played"),
            ("Decks", f"{len(self.stats_data['decks'])} built")
        ]
        
        for i, (label, value) in enumerate(quick_stats):
            box_rect = pygame.Rect(summary_x, summary_y + i * 80, 200, 60)
            self._draw_rounded_rect(self.screen, box_rect, (*self.panel_color[:3], 150), 10)
            
            # Label
            label_text = self.small_font.render(label, True, self.secondary_color)
            label_rect = label_text.get_rect(center=(box_rect.centerx, box_rect.y + 15))
            self.screen.blit(label_text, label_rect)
            
            # Value
            value_text = self.body_font.render(value, True, self.text_color)
            value_rect = value_text.get_rect(center=(box_rect.centerx, box_rect.y + 35))
            self.screen.blit(value_text, value_rect)
