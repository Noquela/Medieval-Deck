#!/usr/bin/env python3
"""
Demo Sprint 2 Visual Enhancements - Medieval Deck

Demonstra as melhorias visuais implementadas:
- Enhanced pulsing glow nas cartas
- Hover effects melhorados
- Animações 30fps
"""

import pygame
import sys
import math
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.card_sprite import CardSprite

def create_demo_card(width=120, height=180, color=(100, 50, 150)):
    """Create a demo card surface."""
    surface = pygame.Surface((width, height))
    surface.fill(color)
    
    # Add card details
    pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), 2)
    
    # Add card name
    font = pygame.font.Font(None, 24)
    text = font.render("Fire Spell", True, (255, 255, 255))
    text_rect = text.get_rect(center=(width//2, 30))
    surface.blit(text, text_rect)
    
    # Add cost
    cost_font = pygame.font.Font(None, 20)
    cost_text = cost_font.render("3", True, (100, 200, 255))
    surface.blit(cost_text, (10, 10))
    
    # Add damage
    damage_text = cost_font.render("⚔️ 4", True, (255, 100, 100))
    surface.blit(damage_text, (width//2 - 15, height//2))
    
    return surface

def main():
    """Run the Sprint 2 visual enhancements demo."""
    pygame.init()
    
    # Set up display
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Sprint 2 Visual Enhancements Demo - Medieval Deck")
    clock = pygame.time.Clock()
    
    # Create demo cards with different types
    card_types = [
        {"color": (100, 50, 150), "name": "Fire Spell", "cost": 3},
        {"color": (150, 50, 100), "name": "Sword Strike", "cost": 2},
        {"color": (50, 150, 100), "name": "Heal", "cost": 2},
        {"color": (50, 100, 150), "name": "Ice Shard", "cost": 2},
        {"color": (150, 100, 50), "name": "Lightning", "cost": 4}
    ]
    
    # Create CardSprites with enhanced effects
    card_sprites = []
    for i, card_type in enumerate(card_types):
        card_surface = create_demo_card(color=card_type["color"])
        x = 100 + i * 200
        y = 300
        card_sprite = CardSprite(card_surface, (x, y))
        card_sprites.append(card_sprite)
    
    # Demo text
    font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 48)
    
    running = True
    demo_time = 0
    
    while running:
        dt = clock.tick(60) / 1000.0
        demo_time += dt
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        
        # Update all card sprites
        for card_sprite in card_sprites:
            card_sprite.update(mouse_pos, dt)
        
        # Clear screen
        screen.fill((20, 30, 50))  # Dark blue background
        
        # Draw title
        title_text = title_font.render("Sprint 2 Visual Enhancements", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(600, 80))
        screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = font.render("Hover over cards to see enhanced pulsing glow effects!", True, (200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(600, 120))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Draw enhancement list
        enhancements = [
            "✨ Enhanced Glow Pulsing with math.sin()",
            "🔥 Multiple Glow Layers (Outer + Inner)",
            "📈 Dynamic Lift & Scale (10-18px, 1.1-1.15x)",
            "⚡ Faster Pulse Rate (0.012 vs 0.008)",
            "🎨 Intensity Range (75-255 alpha)"
        ]
        
        for i, enhancement in enumerate(enhancements):
            enhancement_text = font.render(enhancement, True, (150, 255, 150))
            enhancement_rect = enhancement_text.get_rect(x=50, y=180 + i * 40)
            screen.blit(enhancement_text, enhancement_rect)
        
        # Draw all card sprites with enhanced effects
        for card_sprite in card_sprites:
            card_sprite.draw(screen)
        
        # Draw performance info
        performance_text = font.render(f"FPS: {clock.get_fps():.1f} | Time: {demo_time:.1f}s", True, (255, 255, 100))
        screen.blit(performance_text, (50, 750))
        
        # Show current pulse value for the first card
        if card_sprites:
            first_card = card_sprites[0]
            pulse_value = (math.sin(pygame.time.get_ticks() * 0.012) + 1) * 0.5
            pulse_text = font.render(f"Current Pulse: {pulse_value:.3f} | Alpha: {first_card.outline_alpha}", True, (255, 200, 100))
            screen.blit(pulse_text, (50, 700))
        
        # Instructions
        instructions = [
            "ESC - Exit Demo",
            "Move mouse over cards to see enhanced hover effects",
            "Notice the faster, more intense pulsing glow!"
        ]
        
        for i, instruction in enumerate(instructions):
            instruction_text = font.render(instruction, True, (200, 200, 255))
            instruction_rect = instruction_text.get_rect(x=50, y=600 + i * 25)
            screen.blit(instruction_text, instruction_rect)
        
        pygame.display.flip()
    
    pygame.quit()
    print("🎉 Sprint 2 visual enhancements demo completed!")
    print("✨ Enhanced glow pulsing, dynamic effects, and improved animations!")

if __name__ == "__main__":
    main()
