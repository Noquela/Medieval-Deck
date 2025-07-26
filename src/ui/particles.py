"""
Sistema de partículas para efeitos visuais medievais - Enhanced for P2 Sprint.

Implementa efeitos sutis como:
- Pó mágico flutuante (wizard screen)
- Faíscas douradas (hover em botões)
- Névoas dissipantes (assassin screen)
- Partículas de fogo (knight screen)
- P2: Combat sparks, damage effects, impact particles
"""

import pygame
import random
import math
from typing import List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

from ..ui.theme import theme


class ParticleType(Enum):
    """Tipos de partículas disponíveis."""
    MAGIC_DUST = "magic_dust"
    GOLDEN_SPARKS = "golden_sparks"
    MIST = "mist"
    FIRE_EMBERS = "fire_embers"
    SNOW = "snow"
    LEAVES = "leaves"
    # P2 additions
    DAMAGE_SPARKS = "damage_sparks"
    IMPACT_BURST = "impact_burst"
    HEAL_GLOW = "heal_glow"


@dataclass
class ParticleConfig:
    """P2: Configuration for particle types."""
    velocity_range: Tuple[Tuple[float, float], Tuple[float, float]]  # ((min_x, max_x), (min_y, max_y))
    size_range: Tuple[float, float]
    lifetime_range: Tuple[float, float]
    color: Tuple[int, int, int, int]  # RGBA
    gravity: float = 0.0
    fade_rate: float = 1.0


# P2: Enhanced particle configurations
PARTICLE_CONFIGS = {
    ParticleType.MAGIC_DUST: ParticleConfig(
        velocity_range=((-0.5, 0.5), (-2.0, -0.5)),
        size_range=(1, 3),
        lifetime_range=(3.0, 6.0),
        color=(138, 43, 226, 180),
        fade_rate=0.3
    ),
    ParticleType.GOLDEN_SPARKS: ParticleConfig(
        velocity_range=((-2.0, 2.0), (-2.0, 2.0)),
        size_range=(0.5, 2.0),
        lifetime_range=(1.0, 2.0),
        color=(255, 215, 0, 200),
        fade_rate=0.8
    ),
    ParticleType.DAMAGE_SPARKS: ParticleConfig(
        velocity_range=((-3.0, 3.0), (-4.0, 1.0)),
        size_range=(1.0, 3.0),
        lifetime_range=(0.8, 1.5),
        color=(255, 100, 50, 220),  # Orange-red sparks
        gravity=200.0,
        fade_rate=1.2
    ),
    ParticleType.IMPACT_BURST: ParticleConfig(
        velocity_range=((-4.0, 4.0), (-3.0, 3.0)),
        size_range=(2.0, 5.0),
        lifetime_range=(0.5, 1.0),
        color=(255, 255, 100, 180),  # Bright yellow burst
        gravity=50.0,
        fade_rate=2.0
    ),
    ParticleType.HEAL_GLOW: ParticleConfig(
        velocity_range=((-1.0, 1.0), (-2.0, 0.0)),
        size_range=(2.0, 4.0),
        lifetime_range=(2.0, 3.0),
        color=(100, 255, 100, 150),  # Green healing glow
        gravity=-50.0,  # Float upward
        fade_rate=0.5
    )
}


class Particle:
    """Representa uma partícula individual - Enhanced for P2."""
    
    def __init__(self, x: float, y: float, particle_type: ParticleType):
        self.x = x
        self.y = y
        self.type = particle_type
        
        # Get configuration for this particle type
        config = PARTICLE_CONFIGS.get(particle_type)
        if config:
            # Use P2 configuration system
            vel_x_range, vel_y_range = config.velocity_range
            self.velocity_x = random.uniform(*vel_x_range)
            self.velocity_y = random.uniform(*vel_y_range)
            self.size = random.uniform(*config.size_range)
            self.lifetime = random.uniform(*config.lifetime_range)
            self.color = list(config.color)  # Make mutable for alpha changes
            self.gravity = config.gravity
            self.fade_rate = config.fade_rate
        else:
            # Fallback to legacy setup
            self._setup_properties()
        
        # State
        self.age = 0.0
        self.max_lifetime = self.lifetime
        self.is_alive = True
    
    def _setup_properties(self):
        """Configura propriedades baseadas no tipo de partícula (legacy)."""
        if self.type == ParticleType.MAGIC_DUST:
            self.velocity_x = random.uniform(-0.5, 0.5)
            self.velocity_y = random.uniform(-2.0, -0.5)
            self.size = random.uniform(1, 3)
            self.lifetime = random.uniform(3.0, 6.0)
            self.color = random.choice([
                theme.colors.PURPLE_LIGHT,
                theme.colors.GOLD_LIGHT,
                (138, 43, 226, 180)  # Púrpura com transparência
            ])
            self.fade_rate = 0.3
            
        elif self.type == ParticleType.GOLDEN_SPARKS:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.5, 2.0)
            self.velocity_x = math.cos(angle) * speed
            self.velocity_y = math.sin(angle) * speed
            self.size = random.uniform(0.5, 2.0)
            self.lifetime = random.uniform(1.0, 2.0)
            self.color = random.choice([
                theme.colors.GOLD_LIGHT,
                theme.colors.GOLD_PRIMARY,
                (255, 215, 0, 200)
            ])
            self.fade_rate = 0.8
            
        elif self.type == ParticleType.MIST:
            self.velocity_x = random.uniform(-0.3, 0.3)
            self.velocity_y = random.uniform(-0.5, 0.1)
            self.size = random.uniform(3, 8)
            self.lifetime = random.uniform(4.0, 8.0)
            self.color = (128, 128, 128, 60)  # Cinza translúcido
            self.fade_rate = 0.2
            
        elif self.type == ParticleType.FIRE_EMBERS:
            self.velocity_x = random.uniform(-0.3, 0.3)
            self.velocity_y = random.uniform(-1.5, -0.5)
            self.size = random.uniform(1, 2)
            self.lifetime = random.uniform(2.0, 4.0)
            self.color = random.choice([
                (255, 100, 0, 180),  # Laranja
                (255, 0, 0, 160),    # Vermelho
                (255, 255, 0, 140)   # Amarelo
            ])
            self.fade_rate = 0.5
            
        elif self.type == ParticleType.SNOW:
            self.velocity_x = random.uniform(-0.2, 0.2)
            self.velocity_y = random.uniform(0.5, 1.5)
            self.size = random.uniform(1, 3)
            self.lifetime = random.uniform(5.0, 10.0)
            self.color = (255, 255, 255, 200)
            self.fade_rate = 0.1
            
        else:  # LEAVES
            self.velocity_x = random.uniform(-0.8, 0.8)
            self.velocity_y = random.uniform(0.3, 1.0)
            self.size = random.uniform(2, 4)
            self.lifetime = random.uniform(3.0, 6.0)
            self.color = random.choice([
                (139, 69, 19, 180),  # Marrom
                (34, 139, 34, 160),  # Verde
                (255, 165, 0, 170)   # Laranja
            ])
            self.fade_rate = 0.3
        
        # Propriedades comuns
        self.alpha = 255 if len(self.color) == 3 else self.color[3]
        self.original_alpha = self.alpha
    
    def update(self, dt: float):
        """
        Atualiza partícula - Enhanced for P2.
        
        Args:
            dt: Delta time em segundos
        """
        if not self.is_alive:
            return
        
        # P2: Enhanced physics update
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Apply gravity if present (P2 feature)
        if hasattr(self, 'gravity'):
            self.velocity_y += self.gravity * dt
        
        # Update age and lifetime
        self.age += dt
        
        # P2: Enhanced fade system
        if hasattr(self, 'max_lifetime'):
            life_ratio = self.age / self.max_lifetime
            
            # Apply fade rate (P2)
            fade_rate = getattr(self, 'fade_rate', 1.0)
            if life_ratio > 0.5:  # Start fading at 50% lifetime
                fade_progress = (life_ratio - 0.5) / 0.5
                alpha_multiplier = 1.0 - (fade_progress * fade_rate)
                self.color[3] = int(self.color[3] * max(0, alpha_multiplier))
            
            # Check if particle should die
            if self.age >= self.max_lifetime or self.color[3] <= 0:
                self.is_alive = False
                return
        else:
            # Legacy fade system
            life_ratio = self.age / self.lifetime
            if life_ratio > 0.7:  # Começa a desvanecer aos 70% da vida
                fade_progress = (life_ratio - 0.7) / 0.3
                self.alpha = int(self.original_alpha * (1.0 - fade_progress))
        
        # P2: Enhanced type-specific effects
        if self.type == ParticleType.DAMAGE_SPARKS:
            # Sparks twinkle and lose energy
            self.velocity_x *= 0.95
            self.velocity_y *= 0.95
            if random.random() < 0.3:  # Twinkling effect
                self.color[3] = max(0, self.color[3] - 30)
                
        elif self.type == ParticleType.IMPACT_BURST:
            # Quick burst with rapid fade
            self.velocity_x *= 0.9
            self.velocity_y *= 0.9
            
        elif self.type == ParticleType.HEAL_GLOW:
            # Gentle floating with slight oscillation
            self.x += math.sin(self.age * 3) * 5 * dt
            
        # Legacy effects
        elif self.type == ParticleType.MAGIC_DUST:
            # Movimento serpenteante
            self.x += math.sin(self.age * 2) * 0.5
            
        elif self.type == ParticleType.GOLDEN_SPARKS:
            # Desaceleração gradual
            self.velocity_x *= 0.98
            self.velocity_y *= 0.98
            
        elif self.type == ParticleType.MIST:
            # Expansão lenta
            self.size += dt * 0.5
            
        elif self.type == ParticleType.FIRE_EMBERS:
            # Tremulação
            self.size += math.sin(self.age * 10) * 0.1
            
        # Verifica se ainda está viva
        if self.age >= self.lifetime or self.alpha <= 0:
            self.is_alive = False
    
    def draw(self, surface: pygame.Surface):
        """Desenha partícula na superfície."""
        if not self.is_alive or self.alpha <= 0:
            return
        
        # Cor com alpha atual
        if len(self.color) == 3:
            draw_color = (*self.color, self.alpha)
        else:
            draw_color = (*self.color[:3], min(self.alpha, self.color[3]))
        
        # Cria superfície temporária para transparência
        temp_surface = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        
        if self.type == ParticleType.MIST:
            # Névoa como círculo suave
            pygame.draw.circle(temp_surface, draw_color, 
                             (int(self.size), int(self.size)), int(self.size))
        else:
            # Outras partículas como pontos/círculos pequenos
            pygame.draw.circle(temp_surface, draw_color,
                             (int(self.size), int(self.size)), max(1, int(self.size)))
        
        # Desenha na superfície principal
        surface.blit(temp_surface, (self.x - self.size, self.y - self.size))


class ParticleEmitter:
    """Emissor de partículas para uma região específica - Enhanced for P2."""
    
    def __init__(self,
                 x: float,
                 y: float,
                 width: float,
                 height: float,
                 particle_type: ParticleType,
                 emission_rate: float = 5.0,
                 max_particles: int = 100):
        """
        Inicializa emissor de partículas.
        
        Args:
            x, y: Posição do emissor
            width, height: Área de emissão
            particle_type: Tipo de partículas a emitir
            emission_rate: Partículas por segundo
            max_particles: Máximo de partículas ativas
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.particle_type = particle_type
        self.emission_rate = emission_rate
        self.max_particles = max_particles
        
        self.particles: List[Particle] = []
        self.last_emission = 0.0
        self.is_active = True
        
        # P2: Enhanced emission control
        self.burst_mode = False
        self.one_shot = False
    
    def set_position(self, x: float, y: float):
        """Atualiza posição do emissor."""
        self.x = x
        self.y = y
    
    def set_active(self, active: bool):
        """Ativa/desativa emissor."""
        self.is_active = active
    
    def emit_burst(self, count: int):
        """Emite uma rajada de partículas."""
        for _ in range(count):
            if len(self.particles) < self.max_particles:
                self._create_particle()
                
    def emit_damage(self, count: int = 10):
        """P2: Emit damage sparks effect."""
        old_type = self.particle_type
        self.particle_type = ParticleType.DAMAGE_SPARKS
        self.emit_burst(count)
        self.particle_type = old_type
        
    def emit_impact(self, count: int = 12):
        """P2: Emit impact burst effect."""
        old_type = self.particle_type
        self.particle_type = ParticleType.IMPACT_BURST
        self.emit_burst(count)
        self.particle_type = old_type
        
    def emit_heal(self, count: int = 8):
        """P2: Emit healing glow effect."""
        old_type = self.particle_type
        self.particle_type = ParticleType.HEAL_GLOW
        self.emit_burst(count)
        self.particle_type = old_type
    
    def _create_particle(self):
        """Cria nova partícula na área do emissor."""
        # Posição aleatória na área
        px = self.x + random.uniform(0, self.width)
        py = self.y + random.uniform(0, self.height)
        
        particle = Particle(px, py, self.particle_type)
        self.particles.append(particle)
    
    def update(self, dt: float):
        """
        Atualiza emissor e todas as partículas.
        
        Args:
            dt: Delta time em segundos
        """
        if not theme.enable_particles:
            return
        
        # Emite novas partículas
        if self.is_active:
            self.last_emission += dt
            emission_interval = 1.0 / self.emission_rate
            
            while self.last_emission >= emission_interval and len(self.particles) < self.max_particles:
                self._create_particle()
                self.last_emission -= emission_interval
        
        # Atualiza partículas existentes
        for particle in self.particles[:]:  # Cópia da lista
            particle.update(dt)
            if not particle.is_alive:
                self.particles.remove(particle)
    
    def draw(self, surface: pygame.Surface):
        """Desenha todas as partículas."""
        if not theme.enable_particles:
            return
        
        for particle in self.particles:
            particle.draw(surface)
    
    def clear(self):
        """Remove todas as partículas."""
        self.particles.clear()


class ParticleSystem:
    """
    Sistema simplificado de partículas para a UI de combate.
    """
    
    def __init__(self):
        self.particles = []
        
    def create_impact_effect(self, x: float, y: float):
        """Cria efeito de impacto na posição especificada."""
        # Criar várias partículas de faísca dourada
        for _ in range(random.randint(5, 10)):
            particle = Particle(x, y, ParticleType.GOLDEN_SPARKS)
            # Adicionar velocidade radial
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 50)
            particle.velocity_x = math.cos(angle) * speed
            particle.velocity_y = math.sin(angle) * speed
            self.particles.append(particle)
            
    def update(self, dt: float):
        """Atualiza todas as partículas."""
        for particle in self.particles[:]:  # Cópia da lista
            particle.update(dt)
            if not particle.is_alive:
                self.particles.remove(particle)
                
    def draw(self, surface: pygame.Surface):
        """Desenha todas as partículas."""
        for particle in self.particles:
            particle.draw(surface)


class ParticleManager:
    """Gerenciador global de sistemas de partículas."""
    
    def __init__(self):
        self.emitters: List[ParticleEmitter] = []
    
    def add_emitter(self, emitter: ParticleEmitter):
        """Adiciona emissor ao gerenciador."""
        self.emitters.append(emitter)
    
    def remove_emitter(self, emitter: ParticleEmitter):
        """Remove emissor do gerenciador."""
        if emitter in self.emitters:
            self.emitters.remove(emitter)
    
    def create_magic_dust_emitter(self, x: float, y: float, width: float, height: float) -> ParticleEmitter:
        """Cria emissor de pó mágico para tela do wizard."""
        emitter = ParticleEmitter(
            x, y, width, height,
            ParticleType.MAGIC_DUST,
            emission_rate=3.0,
            max_particles=50
        )
        self.add_emitter(emitter)
        return emitter
    
    def create_mist_emitter(self, x: float, y: float, width: float, height: float) -> ParticleEmitter:
        """Cria emissor de névoa para tela do assassin."""
        emitter = ParticleEmitter(
            x, y, width, height,
            ParticleType.MIST,
            emission_rate=2.0,
            max_particles=30
        )
        self.add_emitter(emitter)
        return emitter
    
    def create_fire_emitters(self, x: float, y: float, width: float, height: float) -> ParticleEmitter:
        """Cria emissor de brasas para tela do knight."""
        emitter = ParticleEmitter(
            x, y, width, height,
            ParticleType.FIRE_EMBERS,
            emission_rate=4.0,
            max_particles=40
        )
        self.add_emitter(emitter)
        return emitter
    
    def create_spark_burst(self, x: float, y: float, count: int = 10):
        """Cria rajada de faíscas douradas (para hover de botões)."""
        emitter = ParticleEmitter(
            x - 10, y - 10, 20, 20,
            ParticleType.GOLDEN_SPARKS,
            emission_rate=0,  # Apenas burst
            max_particles=count
        )
        emitter.emit_burst(count)
        self.add_emitter(emitter)
        
        # Remove emissor após 3 segundos
        import threading
        def remove_later():
            import time
            time.sleep(3)
            self.remove_emitter(emitter)
        
        threading.Thread(target=remove_later, daemon=True).start()
        
    def spawn_hit_particles(self, pos: Tuple[int, int], count: int = 12):
        """Sprint 2-b: Spawn hit particles at position for combat damage."""
        x, y = pos
        emitter = ParticleEmitter(
            x - 15, y - 15, 30, 30,
            ParticleType.DAMAGE_SPARKS,
            emission_rate=0,  # Burst only
            max_particles=count
        )
        emitter.emit_burst(count)
        self.add_emitter(emitter)
        
        # Also add impact burst for extra effect
        impact_emitter = ParticleEmitter(
            x - 10, y - 10, 20, 20,
            ParticleType.IMPACT_BURST,
            emission_rate=0,
            max_particles=8
        )
        impact_emitter.emit_burst(8)
        self.add_emitter(impact_emitter)
        
        # Auto-remove after particles fade
        import threading
        def remove_later():
            import time
            time.sleep(2)
            self.remove_emitter(emitter)
            self.remove_emitter(impact_emitter)
        
        threading.Thread(target=remove_later, daemon=True).start()
    
    def update(self, dt: float):
        """Atualiza todos os emissores."""
        for emitter in self.emitters[:]:  # Cópia da lista
            emitter.update(dt)
            
            # Remove emissores vazios e inativos
            if not emitter.is_active and len(emitter.particles) == 0:
                self.emitters.remove(emitter)
    
    def draw(self, surface: pygame.Surface):
        """Desenha todas as partículas."""
        for emitter in self.emitters:
            emitter.draw(surface)
    
    def clear_all(self):
        """Remove todos os emissores e partículas."""
        for emitter in self.emitters:
            emitter.clear()
        self.emitters.clear()
    
    def set_particles_enabled(self, enabled: bool):
        """Habilita/desabilita sistema de partículas."""
        theme.enable_particles = enabled
        if not enabled:
            self.clear_all()


# Instância global do gerenciador
particle_manager = ParticleManager()
