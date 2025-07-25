"""
Story Screen for Medieval Deck.

Displays character stories and lore with text box navigation.
"""

import pygame
from typing import Dict, List, Optional, Tuple
import logging

from ..utils.config import Config

logger = logging.getLogger(__name__)


class StoryScreen:
    """
    Story screen for displaying character backstories and game lore.
    
    Features:
    - Centered text box with character stories
    - Keyboard navigation (SPACE to advance)
    - Character portraits and themed backgrounds
    - Smooth text animations
    """
    
    def __init__(self, screen: pygame.Surface, config: Config):
        """
        Initialize story screen.
        
        Args:
            screen: Pygame screen surface
            config: Configuration object
        """
        self.screen = screen
        self.config = config
        
        # Screen dimensions
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Text box dimensions
        self.textbox_width = 800
        self.textbox_height = 300
        self.textbox_x = (self.width - self.textbox_width) // 2
        self.textbox_y = self.height - self.textbox_height - 100
        
        # Story data
        self.stories = {
            "warrior": {
                "name": "Sir Gareth the Valiant",
                "portrait_color": (200, 50, 50),
                "chapters": [
                    "In the golden age of the realm, Sir Gareth stood as a beacon of honor among knights. Born to a humble blacksmith, he earned his spurs through courage alone.",
                    "When dragons darkened the skies over Camelshire, Gareth was the first to take up arms. His red banner became a symbol of hope for the common folk.",
                    "Though many battles have weathered his armor, his spirit remains unbroken. For in his heart burns the eternal flame of justice and protection.",
                    "Today, Sir Gareth continues his vigil, defending the innocent and upholding the ancient codes of chivalry that define true knighthood."
                ]
            },
            "wizard": {
                "name": "Archmage Lysander",
                "portrait_color": (100, 50, 200),
                "chapters": [
                    "From the mystical towers of the Celestial Academy, Archmage Lysander has studied the arcane arts for over three centuries.",
                    "His mastery over the elements is legendary - storms bow to his will, and the very fabric of reality bends around his presence.",
                    "Yet with great power comes great responsibility. Lysander has sworn to use his magic only to protect the balance between light and shadow.",
                    "In these troubled times, the Archmage emerges from his tower, ready to face whatever darkness threatens the realm with his ancient wisdom."
                ]
            },
            "assassin": {
                "name": "Shadow of the Crimson Blade",
                "portrait_color": (50, 50, 50),
                "chapters": [
                    "Known only by whispers and feared by tyrants, the Shadow moves through the darkness like death itself, striking down those who abuse their power.",
                    "Once a noble's child, tragedy forged them into something beyond mortal comprehension - a guardian who protects from the shadows.",
                    "Their blade has tasted the blood of corrupt kings and wicked sorcerers alike, yet innocents have nothing to fear from this phantom.",
                    "When justice fails and law becomes tyranny, the Shadow emerges to restore balance through methods both swift and silent."
                ]
            }
        }
        
        # Current story state
        self.current_character = "warrior"
        self.current_chapter = 0
        self.text_animation_progress = 0.0
        self.text_speed = 50  # Characters per second
        
        # Navigation state
        self.character_index = 0
        self.character_list = list(self.stories.keys())
        
        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.name_font = pygame.font.Font(None, 36)
        self.story_font = pygame.font.Font(None, 28)
        self.instruction_font = pygame.font.Font(None, 24)
        
        # Colors
        self.bg_color = tuple(self.config.ui.theme["background_color"])
        self.textbox_color = (20, 20, 30, 220)  # Semi-transparent
        self.text_color = tuple(self.config.ui.theme["text_color"])
        self.accent_color = tuple(self.config.ui.theme["accent_color"])
        self.name_color = tuple(self.config.ui.theme["primary_color"])
        
        # Back button
        self.back_button = pygame.Rect(50, 50, 100, 40)
        
        # Character selection buttons
        self.char_buttons = []
        button_width = 120
        button_spacing = 140
        start_x = (self.width - (len(self.character_list) * button_spacing - 20)) // 2
        
        for i, char in enumerate(self.character_list):
            button_rect = pygame.Rect(start_x + i * button_spacing, 120, button_width, 40)
            self.char_buttons.append({
                "rect": button_rect,
                "character": char,
                "name": char.title()
            })
        
        logger.info("Story screen initialized")
        
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Handle input events.
        
        Args:
            event: Pygame event
            
        Returns:
            Action string if back button clicked, None otherwise
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._advance_story()
            elif event.key == pygame.K_ESCAPE:
                return "back"
            elif event.key == pygame.K_LEFT:
                self._previous_character()
            elif event.key == pygame.K_RIGHT:
                self._next_character()
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.back_button.collidepoint(event.pos):
                    return "back"
                    
                # Check character buttons
                for button in self.char_buttons:
                    if button["rect"].collidepoint(event.pos):
                        self._select_character(button["character"])
                        
                # Click anywhere to advance story
                self._advance_story()
                
        return None
        
    def _advance_story(self) -> None:
        """Advance to next chapter or character."""
        story = self.stories[self.current_character]
        
        # If text is still animating, complete it immediately
        if self.text_animation_progress < 1.0:
            self.text_animation_progress = 1.0
            return
            
        # Advance to next chapter
        if self.current_chapter < len(story["chapters"]) - 1:
            self.current_chapter += 1
            self.text_animation_progress = 0.0
        else:
            # Move to next character
            self._next_character()
            
    def _next_character(self) -> None:
        """Switch to next character."""
        self.character_index = (self.character_index + 1) % len(self.character_list)
        self.current_character = self.character_list[self.character_index]
        self.current_chapter = 0
        self.text_animation_progress = 0.0
        
    def _previous_character(self) -> None:
        """Switch to previous character."""
        self.character_index = (self.character_index - 1) % len(self.character_list)
        self.current_character = self.character_list[self.character_index]
        self.current_chapter = 0
        self.text_animation_progress = 0.0
        
    def _select_character(self, character: str) -> None:
        """Select specific character."""
        if character in self.character_list:
            self.character_index = self.character_list.index(character)
            self.current_character = character
            self.current_chapter = 0
            self.text_animation_progress = 0.0
            
    def update(self, dt: float) -> None:
        """
        Update text animation.
        
        Args:
            dt: Delta time in seconds
        """
        # Animate text appearance
        if self.text_animation_progress < 1.0:
            story = self.stories[self.current_character]
            current_text = story["chapters"][self.current_chapter]
            
            # Calculate how many characters should be visible
            target_chars = len(current_text)
            current_chars = self.text_animation_progress * target_chars
            
            # Advance animation
            self.text_animation_progress += (self.text_speed * dt) / target_chars
            self.text_animation_progress = min(1.0, self.text_animation_progress)
            
    def _draw_rounded_rect(self, surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int, int], radius: int = 10) -> None:
        """Draw a rounded rectangle with alpha."""
        temp_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Draw rounded rectangle
        pygame.draw.rect(temp_surface, color, (radius, 0, rect.width - 2 * radius, rect.height))
        pygame.draw.rect(temp_surface, color, (0, radius, rect.width, rect.height - 2 * radius))
        
        # Draw corners
        pygame.draw.circle(temp_surface, color, (radius, radius), radius)
        pygame.draw.circle(temp_surface, color, (rect.width - radius, radius), radius)
        pygame.draw.circle(temp_surface, color, (radius, rect.height - radius), radius)
        pygame.draw.circle(temp_surface, color, (rect.width - radius, rect.height - radius), radius)
        
        surface.blit(temp_surface, rect.topleft)
        
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """Wrap text to fit within specified width."""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_width = font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
                
        if current_line:
            lines.append(current_line)
            
        return lines
        
    def draw(self) -> None:
        """Draw the story screen."""
        # Clear screen with gradient background
        self.screen.fill(self.bg_color)
        
        # Draw gradient background effect
        for y in range(self.height):
            alpha = int(50 * (y / self.height))
            color = (*self.bg_color, alpha)
            pygame.draw.line(self.screen, self.bg_color, (0, y), (self.width, y))
            
        # Draw title
        title_text = self.title_font.render("Chronicles of the Realm", True, self.accent_color)
        title_rect = title_text.get_rect(center=(self.width // 2, 60))
        self.screen.blit(title_text, title_rect)
        
        # Draw back button
        pygame.draw.rect(self.screen, self.name_color, self.back_button)
        pygame.draw.rect(self.screen, self.accent_color, self.back_button, 2)
        
        back_text = self.instruction_font.render("Back", True, self.text_color)
        back_rect = back_text.get_rect(center=self.back_button.center)
        self.screen.blit(back_text, back_rect)
        
        # Draw character selection buttons
        for i, button in enumerate(self.char_buttons):
            is_selected = button["character"] == self.current_character
            
            # Button color
            if is_selected:
                button_color = self.accent_color
                text_color = self.bg_color
            else:
                button_color = self.name_color
                text_color = self.text_color
                
            pygame.draw.rect(self.screen, button_color, button["rect"])
            pygame.draw.rect(self.screen, self.accent_color, button["rect"], 2)
            
            # Button text
            char_text = self.instruction_font.render(button["name"], True, text_color)
            char_rect = char_text.get_rect(center=button["rect"].center)
            self.screen.blit(char_text, char_rect)
            
        # Draw character portrait (simple colored circle)
        story = self.stories[self.current_character]
        portrait_radius = 80
        portrait_center = (self.width // 2, 250)
        
        pygame.draw.circle(self.screen, story["portrait_color"], portrait_center, portrait_radius)
        pygame.draw.circle(self.screen, self.accent_color, portrait_center, portrait_radius, 3)
        
        # Draw character name
        name_text = self.name_font.render(story["name"], True, self.name_color)
        name_rect = name_text.get_rect(center=(self.width // 2, 350))
        self.screen.blit(name_text, name_rect)
        
        # Draw text box
        textbox_rect = pygame.Rect(self.textbox_x, self.textbox_y, self.textbox_width, self.textbox_height)
        self._draw_rounded_rect(self.screen, textbox_rect, self.textbox_color, 15)
        
        # Draw story text with animation
        current_text = story["chapters"][self.current_chapter]
        
        # Calculate visible text based on animation progress
        visible_chars = int(len(current_text) * self.text_animation_progress)
        animated_text = current_text[:visible_chars]
        
        # Wrap text
        text_margin = 30
        max_text_width = self.textbox_width - 2 * text_margin
        wrapped_lines = self._wrap_text(animated_text, self.story_font, max_text_width)
        
        # Draw text lines
        line_height = self.story_font.get_height() + 5
        start_y = textbox_rect.y + text_margin
        
        for i, line in enumerate(wrapped_lines):
            text_surface = self.story_font.render(line, True, self.text_color)
            self.screen.blit(text_surface, (textbox_rect.x + text_margin, start_y + i * line_height))
            
        # Draw progress indicator
        progress_text = f"Chapter {self.current_chapter + 1}/{len(story['chapters'])}"
        progress_surface = self.instruction_font.render(progress_text, True, self.accent_color)
        progress_rect = progress_surface.get_rect(
            bottomright=(textbox_rect.right - text_margin, textbox_rect.bottom - 10)
        )
        self.screen.blit(progress_surface, progress_rect)
        
        # Draw instructions
        if self.text_animation_progress >= 1.0:
            instruction_text = "Press SPACE to continue, ESC to go back"
        else:
            instruction_text = "Text appearing..."
            
        instruction_surface = self.instruction_font.render(instruction_text, True, self.accent_color)
        instruction_rect = instruction_surface.get_rect(center=(self.width // 2, self.height - 30))
        self.screen.blit(instruction_surface, instruction_rect)
