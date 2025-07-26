"""
Card Sprite - Advanced hover effects with pulsing glow
"""

import pygame
import math
from typing import Tuple, Optional


class CardSprite(pygame.sprite.Sprite):
    """Enhanced card sprite with hover effects and pulsing outline."""
    
    def __init__(self, image: pygame.Surface, pos: Tuple[int, int]):
        super().__init__()
        self.base_image = image.copy()
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)
        self.base_y = pos[1]
        
        # Animation properties
        self.lift = 0
        self.outline_alpha = 0
        self.hover_scale = 1.0
        self.target_lift = 0
        self.target_scale = 1.0
        
        # Hover state
        self.is_hovered = False
        self.hover_time = 0
        
        # Animation smoothing
        self.lift_speed = 0.2
        self.scale_speed = 0.15
        self.alpha_speed = 15
        
    def update(self, mouse_pos: Tuple[int, int], dt: float) -> None:
        """Update hover effects and animations."""
        # Check hover state
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Update hover time for pulse effect
        if self.is_hovered:
            self.hover_time += dt
        else:
            self.hover_time = 0
            
        # Set animation targets with dynamic hover effects
        if self.is_hovered:
            # Base values will be overridden by pulsing calculations below
            pass
        else:
            self.target_lift = 0
            self.target_scale = 1.0
            
        # Smooth animations
        self.lift += (self.target_lift - self.lift) * self.lift_speed
        self.hover_scale += (self.target_scale - self.hover_scale) * self.scale_speed
        
        # Update position
        self.rect.y = int(self.base_y + self.lift)
        
        # Pulsing outline alpha with enhanced intensity
        if self.is_hovered:
            # Enhanced senoidal pulsing effect - faster and more intense
            pulse = (math.sin(pygame.time.get_ticks() * 0.012) + 1) * 0.5
            self.outline_alpha = int(pulse * 180 + 75)  # Range: 75-255
            
            # Dynamic lift based on pulse for extra effect
            base_lift = -15
            pulse_lift = int(pulse * 8)  # Extra 0-8 pixels
            self.target_lift = base_lift - pulse_lift
            
            # Dynamic scale with subtle pulsing
            base_scale = 1.05
            pulse_scale = pulse * 0.03  # Extra 0-0.03 scale
            self.target_scale = base_scale + pulse_scale
        else:
            # Fade out outline
            self.outline_alpha = max(self.outline_alpha - self.alpha_speed, 0)
            self.target_lift = 0
            self.target_scale = 1.0
            
        # Update image scale if needed
        if abs(self.hover_scale - 1.0) > 0.01:
            self._update_scaled_image()
            
    def _update_scaled_image(self) -> None:
        """Update the scaled image based on hover scale."""
        if self.hover_scale != 1.0:
            # Scale the base image
            old_center = self.rect.center
            new_size = (
                int(self.base_image.get_width() * self.hover_scale),
                int(self.base_image.get_height() * self.hover_scale)
            )
            self.image = pygame.transform.smoothscale(self.base_image, new_size)
            self.rect = self.image.get_rect(center=old_center)
        else:
            self.image = self.base_image
            old_center = self.rect.center
            self.rect = self.image.get_rect(center=old_center)
            
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the card with outline effects."""
        # Draw main image
        surface.blit(self.image, self.rect)
        
        # Draw pulsing outline if hovering
        if self.outline_alpha > 0:
            self._draw_outline(surface)
            
    def _draw_outline(self, surface: pygame.Surface) -> None:
        """Draw pulsing outline effect with enhanced glow."""
        if self.outline_alpha <= 0:
            return
            
        # Create multiple glow layers for better effect
        glow_size = max(4, int(self.outline_alpha / 30))
        
        # Outer glow (larger, more transparent)
        outer_glow = pygame.Surface((self.image.get_width() + glow_size*4, 
                                   self.image.get_height() + glow_size*4), pygame.SRCALPHA)
        outer_glow.fill((255, 255, 100, max(20, self.outline_alpha // 4)))
        
        outer_rect = self.rect.copy()
        outer_rect.x -= glow_size*2
        outer_rect.y -= glow_size*2
        surface.blit(outer_glow, outer_rect, special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Inner glow (smaller, more intense)
        inner_glow = pygame.Surface((self.image.get_width() + glow_size*2, 
                                   self.image.get_height() + glow_size*2), pygame.SRCALPHA)
        inner_glow.fill((255, 255, 150, min(255, self.outline_alpha)))
        
        inner_rect = self.rect.copy()
        inner_rect.x -= glow_size
        inner_rect.y -= glow_size
        surface.blit(inner_glow, inner_rect, special_flags=pygame.BLEND_ALPHA_SDL2)
            
    def set_position(self, pos: Tuple[int, int]) -> None:
        """Set new base position for the card."""
        self.rect.topleft = pos
        self.base_y = pos[1]
        
    def get_hover_bounds(self) -> pygame.Rect:
        """Get the bounds including hover effects."""
        return self.rect.inflate(20, 20)  # Add padding for hover detection
        
    def set_hovered(self, hovered: bool) -> None:
        """Set hover state for the card."""
        self.is_hovered = hovered
        if hovered:
            self.target_lift = -20
            self.target_scale = 1.1
        else:
            self.target_lift = 0
            self.target_scale = 1.0
