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
            
        # Set animation targets
        if self.is_hovered:
            self.target_lift = -15
            self.target_scale = 1.05
        else:
            self.target_lift = 0
            self.target_scale = 1.0
            
        # Smooth animations
        self.lift += (self.target_lift - self.lift) * self.lift_speed
        self.hover_scale += (self.target_scale - self.hover_scale) * self.scale_speed
        
        # Update position
        self.rect.y = int(self.base_y + self.lift)
        
        # Pulsing outline alpha
        if self.is_hovered:
            # Senoidal pulsing effect
            pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) * 0.5
            self.outline_alpha = int(pulse * 180 + 75)  # Range: 75-255
        else:
            # Fade out outline
            self.outline_alpha = max(self.outline_alpha - self.alpha_speed, 0)
            
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
        """Draw pulsing outline effect."""
        # Create outline surface
        outline_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        outline_surf.fill((255, 255, 100, self.outline_alpha))  # Golden outline
        
        # Draw outline with offset for glow effect
        offsets = [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2)]
        for dx, dy in offsets:
            outline_rect = self.rect.copy()
            outline_rect.x += dx
            outline_rect.y += dy
            surface.blit(outline_surf, outline_rect, special_flags=pygame.BLEND_ALPHA_SDL2)
            
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
