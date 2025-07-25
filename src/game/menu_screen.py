"""
Menu Screen for Medieval Deck.

Main menu with background, card previews, and smooth animations.
"""

import pygame
import math
from typing import Optional, List, Tuple, Callable
from pathlib import Path
import logging
from PIL import Image, ImageFilter

from ..utils.config import Config
from ..generators.asset_generator import AssetGenerator

logger = logging.getLogger(__name__)


class MenuScreen:
    """
    Main menu screen with animated background and card previews.
    
    Features:
    - Full-screen background with blur effect
    - Animated card previews with hover effects
    - Smooth transitions and animations
    """
    
    def __init__(self, screen: pygame.Surface, config: Config, asset_generator: Optional[AssetGenerator] = None):
        """
        Initialize menu screen.
        
        Args:
            screen: Pygame screen surface
            config: Configuration object
            asset_generator: Asset generator for backgrounds
        """
        self.screen = screen
        self.config = config
        self.asset_generator = asset_generator
        
        # Screen dimensions
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Background
        self.background_surface = None
        self.blur_surface = None
        # Animation states  
        self.animation_time = 0.0
        
        # Simple menu buttons - only 3 main options
        button_width = 250
        button_height = 60
        button_spacing = 80
        start_y = self.height // 2 - 60
        center_x = self.width // 2 - button_width // 2
        
        self.buttons = [
            {"text": "Start Game", "rect": pygame.Rect(center_x, start_y, button_width, button_height), "action": "new_game"},
            {"text": "Settings", "rect": pygame.Rect(center_x, start_y + button_spacing, button_width, button_height), "action": "settings"},
            {"text": "Quit Game", "rect": pygame.Rect(center_x, start_y + (button_spacing * 2), button_width, button_height), "action": "quit_game"},
        ]
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 36)
        self.card_font = pygame.font.Font(None, 24)
        
        # Colors
        self.bg_color = tuple(self.config.ui.theme["background_color"])
        self.primary_color = tuple(self.config.ui.theme["primary_color"])
        self.text_color = tuple(self.config.ui.theme["text_color"])
        self.accent_color = tuple(self.config.ui.theme["accent_color"])
        
        # Load background
        self._load_background()
        # Remove card previews from main menu - they belong in character selection
        # self._load_card_previews()
        
        logger.info("Menu screen initialized")
        
    def _load_background(self) -> None:
        """Load and prepare background image with blur effect."""
        if not self.asset_generator:
            # Create default background
            self.background_surface = pygame.Surface((self.width, self.height))
            self.background_surface.fill(self.bg_color)
            self.blur_surface = self.background_surface.copy()
            return
            
        try:
            # Generate or load background
            background_image = self.asset_generator.generate_background()
            
            # Convert PIL to pygame surface
            pil_image = background_image.resize((self.width, self.height), Image.LANCZOS)
            
            # Create blur version
            blur_image = pil_image.filter(ImageFilter.GaussianBlur(radius=3))
            
            # Convert to pygame surfaces
            self.background_surface = self._pil_to_pygame(pil_image)
            self.blur_surface = self._pil_to_pygame(blur_image)
            
            logger.info("Background loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load background: {e}")
            # Fallback to solid color
            self.background_surface = pygame.Surface((self.width, self.height))
            self.background_surface.fill(self.bg_color)
            self.blur_surface = self.background_surface.copy()
            
    def _pil_to_pygame(self, pil_image: Image.Image) -> pygame.Surface:
        """Convert PIL image to pygame surface."""
        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tobytes()
        
        if mode == "RGB":
            surface = pygame.image.fromstring(data, size, mode)
        elif mode == "RGBA":
            surface = pygame.image.fromstring(data, size, mode)
            surface = surface.convert_alpha()
        else:
            # Convert to RGB first
            rgb_image = pil_image.convert("RGB")
            data = rgb_image.tobytes()
            surface = pygame.image.fromstring(data, size, "RGB")
            
        return surface
        
    def _load_card_previews(self) -> None:
        """Load card preview images."""
        if not self.asset_generator:
            # Create placeholder cards
            for preview in self.card_previews:
                card_surface = pygame.Surface((150, 210))
                card_surface.fill(self.primary_color)
                
                # Add text
                text = self.card_font.render(preview["name"], True, self.text_color)
                text_rect = text.get_rect(center=(75, 105))
                card_surface.blit(text, text_rect)
                
                self.card_surfaces[preview["type"]] = card_surface
            return
            
        try:
            for preview in self.card_previews:
                card_type = preview["type"]
                
                # Generate or load card image
                card_image = self.asset_generator.generate_card_image(card_type)
                
                # Resize to card dimensions
                card_width = self.config.ui.card_width
                card_height = self.config.ui.card_height
                pil_card = card_image.resize((card_width, card_height), Image.LANCZOS)
                
                # Convert to pygame surface
                card_surface = self._pil_to_pygame(pil_card)
                
                # Add card frame
                frame_surface = pygame.Surface((card_width + 4, card_height + 4))
                frame_surface.fill(self.accent_color)
                frame_surface.blit(card_surface, (2, 2))
                
                self.card_surfaces[card_type] = frame_surface
                
        except Exception as e:
            logger.error(f"Failed to load card previews: {e}")
            # Create placeholder surfaces instead of recursion
            for card_type in ["creature", "spell", "artifact"]:
                placeholder = pygame.Surface((self.config.ui.card_width, self.config.ui.card_height))
                placeholder.fill((100, 100, 100))  # Gray placeholder
                self.card_surfaces[card_type] = placeholder
            
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handle input events.
        
        Args:
            event: Pygame event
            
        Returns:
            Action string if button clicked, None otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                
                # Check button clicks
                for button in self.buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        return button["action"]
                        
        # Remove card handling - cards belong in character selection
        return None
        
    def _get_card_rect(self, preview: dict) -> pygame.Rect:
        """Get rectangle for card preview."""
        card_width = self.config.ui.card_width
        card_height = self.config.ui.card_height
        
        return pygame.Rect(
            preview["pos"][0] - card_width // 2,
            preview["pos"][1] - card_height // 2,
            card_width,
            card_height
        )
        
    def _animate_card_click(self, preview: dict) -> None:
        """Animate card click with slide to center."""
        center_x = self.width // 2
        center_y = self.height // 2
        
        preview["target_pos"] = [center_x, center_y]
        self.selected_card = preview["type"]
        
    def update(self, dt: float) -> None:
        """
        Update animations.
        
        Args:
            dt: Delta time in seconds
        """
        self.animation_time += dt
        
        # Simple animation time update - no card previews in main menu
            
    def draw(self) -> None:
        """Draw the menu screen."""
        # Draw background
        self.screen.blit(self.background_surface, (0, 0))
            
        # Draw semi-transparent overlay for readability
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Draw title
        title_text = self.title_font.render("Medieval Deck", True, self.accent_color)
        title_rect = title_text.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Draw menu buttons
        for button in self.buttons:
            # Button background
            pygame.draw.rect(self.screen, self.primary_color, button["rect"])
            pygame.draw.rect(self.screen, self.accent_color, button["rect"], 2)
            
            # Button text
            text = self.button_font.render(button["text"], True, self.text_color)
            text_rect = text.get_rect(center=button["rect"].center)
            self.screen.blit(text, text_rect)
