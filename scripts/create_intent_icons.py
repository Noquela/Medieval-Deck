#!/usr/bin/env python3
"""
Create intent icons for enemy actions.
"""

import pygame
import math
from pathlib import Path

def create_sword_icon():
    """Create sword icon for attack intent."""
    size = 32
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Sword blade (vertical)
    blade_rect = pygame.Rect(14, 4, 4, 20)
    pygame.draw.rect(surface, (200, 200, 200), blade_rect)
    
    # Crossguard
    crossguard_rect = pygame.Rect(10, 22, 12, 2)
    pygame.draw.rect(surface, (150, 150, 150), crossguard_rect)
    
    # Handle
    handle_rect = pygame.Rect(14, 24, 4, 6)
    pygame.draw.rect(surface, (139, 69, 19), handle_rect)
    
    # Pommel
    pygame.draw.circle(surface, (100, 100, 100), (16, 30), 2)
    
    return surface

def create_shield_icon():
    """Create shield icon for defense intent."""
    size = 32
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Shield outline (rounded rectangle)
    center_x, center_y = size // 2, size // 2
    width, height = 20, 24
    
    # Main shield body
    shield_rect = pygame.Rect(center_x - width//2, center_y - height//2, width, height)
    pygame.draw.rect(surface, (100, 150, 200), shield_rect, border_radius=4)
    
    # Shield border
    pygame.draw.rect(surface, (80, 120, 180), shield_rect, 2, border_radius=4)
    
    # Cross pattern
    # Vertical line
    pygame.draw.line(surface, (80, 120, 180), 
                    (center_x, center_y - height//3), 
                    (center_x, center_y + height//3), 2)
    # Horizontal line  
    pygame.draw.line(surface, (80, 120, 180), 
                    (center_x - width//3, center_y), 
                    (center_x + width//3, center_y), 2)
    
    return surface

def main():
    """Create intent icons."""
    pygame.init()
    
    assets_ui_dir = Path("assets/ui")
    assets_ui_dir.mkdir(exist_ok=True)
    
    # Create sword icon
    sword_icon = create_sword_icon()
    pygame.image.save(sword_icon, assets_ui_dir / "icon_sword.png")
    print("✅ Created icon_sword.png")
    
    # Create shield icon
    shield_icon = create_shield_icon()
    pygame.image.save(shield_icon, assets_ui_dir / "icon_shield.png")
    print("✅ Created icon_shield.png")
    
    print("🎨 Intent icons created successfully!")

if __name__ == "__main__":
    main()
