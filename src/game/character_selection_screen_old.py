"""
Character Selection Screen for Medieval Deck.

Shows available characters/cards for player selection.
"""

import pygame
import math
import logging
from typing import Optional, List, Tuple, Dict
from pathlib import Path
from PIL import Image
import logging
from PIL import Image

from ..utils.config import Config
from ..generators.asset_generator import AssetGenerator

logger = logging.getLogger(__name__)


class CharacterSelectionScreen:
    """
    Character selection screen with character cards and previews.
    
    Features:
    - Character card previews with hover effects
    - Character details and stats
    - Back to menu and confirm selection buttons
    """
    
    def __init__(self, screen: pygame.Surface, config: Config, asset_generator: Optional[AssetGenerator] = None):
        """
        Initialize character selection screen.
        
        Args:
            screen: Pygame screen surface
            config: Game configuration
            asset_generator: Asset generator for images
        """
        self.screen = screen
        self.config = config
        self.asset_generator = asset_generator
        
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Animation properties
        self.animation_time = 0.0
        self.hovered_character = None
        self.selected_character = None
        
        # UI elements
        self.buttons = []
        self.character_cards = []
        self.character_surfaces = {}
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 36)
        self.character_font = pygame.font.Font(None, 24)
        
        # Colors from theme
        self.bg_color = tuple(self.config.ui.theme["background_color"])
        self.primary_color = tuple(self.config.ui.theme["primary_color"])
        self.text_color = tuple(self.config.ui.theme["text_color"])
        self.accent_color = tuple(self.config.ui.theme["accent_color"])
        
        # Initialize
        self._setup_ui()
        self._load_character_cards()
        
        logger.info("Character selection screen initialized")
        
    def _setup_ui(self) -> None:
        """Setup UI elements and buttons."""
        # Back button
        back_button = pygame.Rect(50, 50, 120, 50)
        self.buttons.append({
            "rect": back_button,
            "text": "Back",
            "action": "back_to_menu"
        })
        
        # Confirm button (initially disabled)
        confirm_button = pygame.Rect(self.width - 170, self.height - 100, 120, 50)
        self.buttons.append({
            "rect": confirm_button,
            "text": "Select",
            "action": "confirm_selection",
            "enabled": False
        })
        
        # Character card positions (3 characters in a row)
        card_spacing = 200
        start_x = (self.width - (3 * card_spacing)) // 2 + card_spacing // 2
        start_y = self.height // 2
        
        characters = [
            {
                "name": "Valiant Knight", 
                "type": "knight_01", 
                "description": "A brave warrior with strong defense",
                "stats": {
                    "Health": 30,
                    "Attack": 8,
                    "Defense": 12,
                    "Magic": 3,
                    "Speed": 6
                },
                "abilities": ["Shield Wall", "Charge Attack", "Taunt"],
                "background_type": "castle"
            },
            {
                "name": "Arcane Wizard", 
                "type": "wizard_01", 
                "description": "Master of magical arts and spells",
                "stats": {
                    "Health": 20,
                    "Attack": 5,
                    "Defense": 6,
                    "Magic": 15,
                    "Speed": 8
                },
                "abilities": ["Fireball", "Ice Shield", "Teleport"],
                "background_type": "wizard"
            }, 
            {
                "name": "Shadow Assassin", 
                "type": "assassin_01", 
                "description": "Swift and deadly in the shadows",
                "stats": {
                    "Health": 25,
                    "Attack": 12,
                    "Defense": 7,
                    "Magic": 6,
                    "Speed": 14
                },
                "abilities": ["Stealth", "Poison Blade", "Critical Strike"],
                "background_type": "forest"
            }
        ]
        
        for i, character in enumerate(characters):
            x = start_x + (i * card_spacing)
            y = start_y
            
            self.character_cards.append({
                "name": character["name"],
                "type": character["type"],
                "description": character["description"],
                "pos": [x, y],
                "rect": pygame.Rect(x - 75, y - 105, 150, 210)
            })
    
    def _load_character_cards(self) -> None:
        """Load character card images."""
        try:
            for character in self.character_cards:
                char_type = character["type"]
                
                if self.asset_generator:
                    # Try to load existing character image
                    char_image = self.asset_generator.generate_card_image(char_type, force_regenerate=False)
                    
                    # Resize to card dimensions
                    card_width = self.config.ui.card_width
                    card_height = self.config.ui.card_height
                    pil_card = char_image.resize((card_width, card_height), Image.LANCZOS)
                    
                    # Convert to pygame surface
                    card_surface = pygame.image.fromstring(
                        pil_card.tobytes(), pil_card.size, pil_card.mode
                    )
                else:
                    # Create placeholder
                    card_surface = pygame.Surface((self.config.ui.card_width, self.config.ui.card_height))
                    card_surface.fill((80, 80, 120))  # Blue-gray placeholder
                
                # Add frame
                frame_surface = pygame.Surface((card_surface.get_width() + 4, card_surface.get_height() + 4))
                frame_surface.fill(self.accent_color)
                frame_surface.blit(card_surface, (2, 2))
                
                self.character_surfaces[char_type] = frame_surface
                
        except Exception as e:
            logger.error(f"Failed to load character cards: {e}")
            # Create placeholder surfaces
            for character in self.character_cards:
                char_type = character["type"]
                placeholder = pygame.Surface((self.config.ui.card_width, self.config.ui.card_height))
                placeholder.fill((100, 100, 100))  # Gray placeholder
                self.character_surfaces[char_type] = placeholder
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handle input events.
        
        Args:
            event: Pygame event
            
        Returns:
            Action string if action taken, None otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                
                # Check button clicks
                for button in self.buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        if button.get("enabled", True):
                            return button["action"]
                
                # Check character card clicks
                for character in self.character_cards:
                    if character["rect"].collidepoint(mouse_pos):
                        # Ir direto para a tela individual do personagem
                        character_type = character["type"]
                        return f"show_character_{character_type}"
                        
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            
            # Update hovered character
            self.hovered_character = None
            for character in self.character_cards:
                if character["rect"].collidepoint(mouse_pos):
                    self.hovered_character = character["type"]
                    break
        
        return None
    
    def update(self, dt: float) -> None:
        """
        Update animations.
        
        Args:
            dt: Delta time in seconds
        """
        self.animation_time += dt
    
    def draw(self) -> None:
        """Draw the character selection screen."""
        # Clear screen with background
        self.screen.fill(self.bg_color)
        
        # Draw character-specific background if one is selected
        if self.selected_character:
            self._draw_character_background()
        
        # Draw title
        title_text = self.title_font.render("Select Your Character", True, self.accent_color)
        title_rect = title_text.get_rect(center=(self.width // 2, 60))
        self.screen.blit(title_text, title_rect)
        
        # Draw character cards
        for character in self.character_cards:
            char_type = character["type"]
            
            if char_type not in self.character_surfaces:
                continue
                
            card_surface = self.character_surfaces[char_type]
            
            # Apply hover effect
            if self.hovered_character == char_type:
                hover_scale = self.config.ui.card_hover_scale
                scaled_width = int(card_surface.get_width() * hover_scale)
                scaled_height = int(card_surface.get_height() * hover_scale)
                card_surface = pygame.transform.scale(card_surface, (scaled_width, scaled_height))
                
                # Add subtle rotation
                rotation_angle = math.sin(self.animation_time * 3) * 2
                card_surface = pygame.transform.rotate(card_surface, rotation_angle)
            
            # Highlight selected character
            if self.selected_character == char_type:
                # Add golden glow effect
                glow_surface = pygame.Surface((card_surface.get_width() + 10, card_surface.get_height() + 10))
                glow_surface.fill((255, 215, 0))  # Gold color
                glow_rect = glow_surface.get_rect(center=character["pos"])
                self.screen.blit(glow_surface, glow_rect)
            
            # Draw card
            card_rect = card_surface.get_rect(center=character["pos"])
            self.screen.blit(card_surface, card_rect)
            
            # Draw character name
            name_text = self.character_font.render(character["name"], True, self.text_color)
            name_rect = name_text.get_rect(center=(character["pos"][0], character["pos"][1] + 130))
            
            # Text background for readability
            text_bg = pygame.Surface((name_text.get_width() + 10, name_text.get_height() + 4))
            text_bg.set_alpha(150)
            text_bg.fill((0, 0, 0))
            text_bg_rect = text_bg.get_rect(center=name_rect.center)
            
            self.screen.blit(text_bg, text_bg_rect)
            self.screen.blit(name_text, name_rect)
        
        # Draw character details if one is selected
        if self.selected_character:
            self._draw_character_details()
        
        # Draw buttons
        for button in self.buttons:
            enabled = button.get("enabled", True)
            button_color = self.primary_color if enabled else (100, 100, 100)
            text_color = self.text_color if enabled else (150, 150, 150)
            
            # Button background
            pygame.draw.rect(self.screen, button_color, button["rect"])
            pygame.draw.rect(self.screen, self.accent_color, button["rect"], 2)
            
            # Button text
            text = self.button_font.render(button["text"], True, text_color)
            text_rect = text.get_rect(center=button["rect"].center)
            self.screen.blit(text, text_rect)
    
    def _draw_character_background(self) -> None:
        """Draw character-specific background."""
        if not self.asset_generator:
            return
            
        try:
            # Get background based on selected character type
            bg_image = None
            for character in self.character_cards:
                if character["type"] == self.selected_character:
                    bg_type = character.get("background_type", character["type"])
                    bg_image = self.asset_generator.generate_card_image(bg_type, force_regenerate=False)
                    break
            
            if bg_image:
                # Scale background to screen size
                bg_resized = bg_image.resize((self.width, self.height), Image.LANCZOS)
                bg_surface = pygame.image.fromstring(
                    bg_resized.tobytes(), bg_resized.size, bg_resized.mode
                )
                
                # Apply transparency overlay
                overlay = pygame.Surface((self.width, self.height))
                overlay.set_alpha(180)  # Make it semi-transparent
                overlay.fill((0, 0, 0))
                
                self.screen.blit(bg_surface, (0, 0))
                self.screen.blit(overlay, (0, 0))
                
        except Exception as e:
            logger.error(f"Failed to draw character background: {e}")
    
    def _draw_character_details(self) -> None:
        """Draw detailed character information panel."""
        # Find selected character data
        selected_char_data = None
        for character in self.character_cards:
            if character["type"] == self.selected_character:
                selected_char_data = character
                break
        
        if not selected_char_data:
            return
        
        # Details panel dimensions
        panel_width = 350
        panel_height = 400
        panel_x = self.width - panel_width - 30
        panel_y = 120
        
        # Draw panel background
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill((40, 40, 60))  # Dark blue-gray
        
        # Panel border
        pygame.draw.rect(self.screen, self.accent_color, 
                        (panel_x, panel_y, panel_width, panel_height), 3)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # Character name (title)
        y_offset = 20
        name_text = self.title_font.render(selected_char_data["name"], True, self.accent_color)
        if name_text.get_width() > panel_width - 20:
            # Use smaller font if name is too long
            name_text = self.button_font.render(selected_char_data["name"], True, self.accent_color)
        name_rect = pygame.Rect(panel_x + 10, panel_y + y_offset, panel_width - 20, 40)
        self.screen.blit(name_text, (panel_x + 15, panel_y + y_offset))
        y_offset += 50
        
        # Description
        desc_text = self.character_font.render("Description:", True, self.text_color)
        self.screen.blit(desc_text, (panel_x + 15, panel_y + y_offset))
        y_offset += 25
        
        # Wrap description text
        desc_lines = self._wrap_text(selected_char_data["description"], panel_width - 30)
        for line in desc_lines:
            line_text = self.character_font.render(line, True, (200, 200, 200))
            self.screen.blit(line_text, (panel_x + 15, panel_y + y_offset))
            y_offset += 20
        
        y_offset += 15
        
        # Stats table
        stats_title = self.character_font.render("Statistics:", True, self.text_color)
        self.screen.blit(stats_title, (panel_x + 15, panel_y + y_offset))
        y_offset += 25
        
        stats = selected_char_data.get("stats", {})
        for stat_name, stat_value in stats.items():
            # Stat name
            stat_text = self.character_font.render(f"{stat_name}:", True, (180, 180, 180))
            self.screen.blit(stat_text, (panel_x + 20, panel_y + y_offset))
            
            # Stat value
            value_text = self.character_font.render(str(stat_value), True, self.accent_color)
            self.screen.blit(value_text, (panel_x + 120, panel_y + y_offset))
            
            # Stat bar
            bar_x = panel_x + 160
            bar_y = panel_y + y_offset + 5
            bar_width = 150
            bar_height = 12
            
            # Background bar
            pygame.draw.rect(self.screen, (100, 100, 100), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            # Filled bar (assuming max stat is 20)
            fill_width = int((stat_value / 20.0) * bar_width)
            fill_color = self._get_stat_color(stat_name)
            pygame.draw.rect(self.screen, fill_color, 
                           (bar_x, bar_y, fill_width, bar_height))
            
            # Bar border
            pygame.draw.rect(self.screen, self.text_color, 
                           (bar_x, bar_y, bar_width, bar_height), 1)
            
            y_offset += 25
        
        y_offset += 15
        
        # Abilities
        abilities_title = self.character_font.render("Abilities:", True, self.text_color)
        self.screen.blit(abilities_title, (panel_x + 15, panel_y + y_offset))
        y_offset += 25
        
        abilities = selected_char_data.get("abilities", [])
        for ability in abilities:
            ability_text = self.character_font.render(f"• {ability}", True, (180, 180, 180))
            self.screen.blit(ability_text, (panel_x + 20, panel_y + y_offset))
            y_offset += 20
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within max_width pixels."""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            test_surface = self.character_font.render(test_line, True, (255, 255, 255))
            
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _get_stat_color(self, stat_name: str) -> Tuple[int, int, int]:
        """Get color for stat bar based on stat type."""
        colors = {
            "Health": (220, 60, 60),     # Red
            "Attack": (220, 120, 60),    # Orange  
            "Defense": (60, 120, 220),   # Blue
            "Magic": (160, 60, 220),     # Purple
            "Speed": (60, 220, 120),     # Green
        }
        return colors.get(stat_name, (150, 150, 150))  # Gray default
    
    def get_selected_character(self) -> Optional[str]:
        """Get the currently selected character type."""
        return self.selected_character
