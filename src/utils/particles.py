"""
Particle system - Minimalista e seguro
"""

import pygame
import random
from typing import List, Dict, Any


class ParticleEmitter:
    """Particle emitter minimalista e seguro."""
    
    def __init__(self, pos, color=(255, 215, 0), n=12, life=0.4):
        """
        Initialize particle emitter.
        
        Args:
            pos: Position tuple (x, y)
            color: RGB color tuple
            n: Number of particles
            life: Particle lifetime in seconds
        """
        self.particles = []
        for _ in range(n):
            self.particles.append({
                "pos": pygame.Vector2(pos),
                "vel": pygame.Vector2(
                    random.uniform(-80, 80),
                    random.uniform(-120, -40)
                ),
                "life": life,
                "max_life": life,
                "color": color
            })
    
    def update(self, dt):
        """Update particles."""
        for particle in self.particles[:]:
            # Update position
            particle["pos"] += particle["vel"] * dt
            
            # Update life
            particle["life"] -= dt
            
            # Apply gravity
            particle["vel"].y += 200 * dt
            
            # Remove dead particles
            if particle["life"] <= 0:
                self.particles.remove(particle)
    
    def draw(self, surf):
        """Draw particles."""
        for particle in self.particles:
            # Calculate alpha based on remaining life
            alpha = int(255 * (particle["life"] / particle["max_life"]))
            alpha = max(0, min(255, alpha))
            
            # Create particle surface
            particle_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            color_with_alpha = (*particle["color"][:3], alpha)
            particle_surf.fill(color_with_alpha)
            
            # Draw particle
            surf.blit(particle_surf, particle["pos"])
    
    @property
    def alive(self):
        """Check if emitter has any living particles."""
        return bool(self.particles)
