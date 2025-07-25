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
        
        # Simple menu buttons - now with combat test option
        button_width = 250
        button_height = 60
        button_spacing = 80
        start_y = self.height // 2 - 80
        center_x = self.width // 2 - button_width // 2
        
        self.buttons = [
            {"text": "Start Game", "rect": pygame.Rect(center_x, start_y, button_width, button_height), "action": "new_game"},
            {"text": "Combat Test", "rect": pygame.Rect(center_x, start_y + button_spacing, button_width, button_height), "action": "combat_test"},
            {"text": "Settings", "rect": pygame.Rect(center_x, start_y + (button_spacing * 2), button_width, button_height), "action": "settings"},
            {"text": "Quit Game", "rect": pygame.Rect(center_x, start_y + (button_spacing * 3), button_width, button_height), "action": "quit_game"},
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
        """Carrega background do menu gerado por IA com efeito de blur."""
        if not self.asset_generator:
            # Criar background padrão quando IA não está disponível
            self.background_surface = pygame.Surface((self.width, self.height))
            self.background_surface.fill(self.bg_color)
            self.blur_surface = self.background_surface.copy()
            logger.info("Background padrão criado (IA não disponível)")
            return
            
        try:
            # Gerar ou carregar background do menu com IA
            logger.info("Carregando background do menu gerado por IA...")
            background_image = self.asset_generator.generate_menu_background()
            
            if background_image is None:
                # Fallback se não conseguir gerar
                self.background_surface = pygame.Surface((self.width, self.height))
                self.background_surface.fill(self.bg_color)
                logger.warning("Não foi possível gerar background, usando cor sólida")
                return
            
            # Converter PIL para surface do Pygame
            pil_image = background_image.resize((self.width, self.height), Image.LANCZOS)
            
            # Aplicar blur leve para efeito atmosférico
            import PIL.ImageFilter
            blurred_image = pil_image.filter(PIL.ImageFilter.GaussianBlur(radius=2))
            
            # Converter para Surface do Pygame
            mode = blurred_image.mode
            size = blurred_image.size
            data = blurred_image.tobytes()
            
            self.background_surface = pygame.image.fromstring(data, size, mode).convert()
            
            # Criar overlay escuro para melhorar legibilidade do texto
            overlay = pygame.Surface((self.width, self.height))
            overlay.set_alpha(80)  # 30% de transparência
            overlay.fill((0, 0, 0))
            
            # Aplicar overlay no background
            self.background_surface.blit(overlay, (0, 0))
            
            # Criar versão ainda mais escura para transições
            self.blur_surface = self.background_surface.copy()
            dark_overlay = pygame.Surface((self.width, self.height))
            dark_overlay.set_alpha(120)  # 50% de transparência adicional
            dark_overlay.fill((0, 0, 0))
            self.blur_surface.blit(dark_overlay, (0, 0))
            
            logger.info("Background do menu carregado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao carregar background do menu: {e}")
            # Fallback para background padrão
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
        
    def enter_screen(self) -> None:
        """Chamado quando a tela é ativada - sempre recarrega background."""
        logger.info("Entrando na tela do menu...")
        if self.asset_generator:
            logger.info("Recarregando background do menu...")
            self._load_background()
        else:
            logger.warning("Asset generator não disponível para recarregar background")
            
    def draw(self) -> None:
        """Draw the menu screen."""
        # Draw background
        if self.background_surface:
            self.screen.blit(self.background_surface, (0, 0))
        else:
            # Fallback background
            self.screen.fill(self.bg_color)
            
        # Draw semi-transparent overlay for readability
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Draw title with golden medieval style
        title_text = self.title_font.render("Medieval Deck", True, (255, 215, 0))  # Golden color
        title_rect = title_text.get_rect(center=(self.width // 2, 80))
        
        # Add glow effect to title
        glow_text = self.title_font.render("Medieval Deck", True, (255, 255, 100))
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx != 0 or dy != 0:
                    glow_rect = title_rect.copy()
                    glow_rect.x += dx
                    glow_rect.y += dy
                    self.screen.blit(glow_text, glow_rect)
        
        self.screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.button_font.render("AI-Generated Medieval Card Game", True, (245, 245, 220))  # Parchment color
        subtitle_rect = subtitle_text.get_rect(center=(self.width // 2, 130))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw menu buttons with medieval styling
        for i, button in enumerate(self.buttons):
            # Button shadow
            shadow_rect = button["rect"].copy()
            shadow_rect.x += 3
            shadow_rect.y += 3
            pygame.draw.rect(self.screen, (0, 0, 0), shadow_rect)
            
            # Button background with gradient effect
            base_color = (47, 47, 47)  # Dark stone
            highlight_color = (105, 105, 105)  # Light stone
            
            # Create gradient effect
            for y in range(button["rect"].height):
                blend_factor = y / button["rect"].height
                r = int(base_color[0] + (highlight_color[0] - base_color[0]) * blend_factor)
                g = int(base_color[1] + (highlight_color[1] - base_color[1]) * blend_factor)
                b = int(base_color[2] + (highlight_color[2] - base_color[2]) * blend_factor)
                
                line_rect = pygame.Rect(button["rect"].x, button["rect"].y + y, button["rect"].width, 1)
                pygame.draw.rect(self.screen, (r, g, b), line_rect)
            
            # Button border with golden accent
            pygame.draw.rect(self.screen, (218, 165, 32), button["rect"], 3)  # Golden border
            
            # Button text with medieval styling
            text = self.button_font.render(button["text"], True, (245, 245, 220))  # Parchment color
            text_rect = text.get_rect(center=button["rect"].center)
            
            # Text shadow
            shadow_text = self.button_font.render(button["text"], True, (0, 0, 0))
            shadow_text_rect = text_rect.copy()
            shadow_text_rect.x += 1
            shadow_text_rect.y += 1
            self.screen.blit(shadow_text, shadow_text_rect)
            
            self.screen.blit(text, text_rect)
