"""
Medieval Deck - Sistema de Animação de Sprite Sheets

Geração automática de animações 30fps com IA e reprodução fluida.
"""

import pygame
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class FrameAnimation:
    """
    Reproduz animação de sprite sheet a 30 fps com controle de loop.
    """
    
    def __init__(self, frames: List[pygame.Surface], fps: int = 30, loop: bool = True):
        """
        Inicializa animação de frames.
        
        Args:
            frames: Lista de surfaces dos quadros
            fps: Frames por segundo
            loop: Se deve repetir a animação
        """
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.timer = 0.0
        self.current_frame = 0
        self.finished = False
        
    def update(self, dt: float):
        """
        Atualiza o timer e frame atual.
        
        Args:
            dt: Delta time em segundos
        """
        if self.finished and not self.loop:
            return
            
        self.timer += dt
        frame_duration = 1.0 / self.fps
        total_duration = len(self.frames) * frame_duration
        
        if self.loop:
            # Loop infinito
            self.timer = self.timer % total_duration
        else:
            # Uma vez só
            if self.timer >= total_duration:
                self.timer = total_duration - frame_duration
                self.finished = True
        
        # Calcular frame atual
        self.current_frame = min(int(self.timer * self.fps), len(self.frames) - 1)
        
    def current(self) -> pygame.Surface:
        """
        Retorna o frame atual da animação.
        
        Returns:
            Surface do frame atual
        """
        if not self.frames:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        return self.frames[self.current_frame]
        
    def reset(self):
        """Reinicia a animação do início."""
        self.timer = 0.0
        self.current_frame = 0
        self.finished = False
        
    def is_finished(self) -> bool:
        """Retorna True se animação não-loop terminou."""
        return self.finished


class AnimationManager:
    """
    Gerencia múltiplas animações por entidade.
    """
    
    def __init__(self):
        self.animations = {}  # entity_id -> {action -> FrameAnimation}
        self.current_animations = {}  # entity_id -> current_action
        
    def add_animation(self, entity_id: str, action: str, frames: List[pygame.Surface], 
                     fps: int = 30, loop: bool = True):
        """
        Adiciona animação para uma entidade.
        
        Args:
            entity_id: ID da entidade
            action: Nome da ação (idle, attack, etc)
            frames: Lista de frames
            fps: Frames por segundo
            loop: Se deve fazer loop
        """
        if entity_id not in self.animations:
            self.animations[entity_id] = {}
            
        self.animations[entity_id][action] = FrameAnimation(frames, fps, loop)
        
        # Se é a primeira animação, definir como atual
        if entity_id not in self.current_animations:
            self.current_animations[entity_id] = action
            
    def play_animation(self, entity_id: str, action: str, force_restart: bool = False):
        """
        Inicia uma animação específica.
        
        Args:
            entity_id: ID da entidade
            action: Nome da ação
            force_restart: Se deve reiniciar mesmo se já está tocando
        """
        if entity_id not in self.animations or action not in self.animations[entity_id]:
            logger.warning(f"Animation {action} not found for entity {entity_id}")
            return
            
        # Se já está tocando esta animação e não é para forçar restart
        if not force_restart and self.current_animations.get(entity_id) == action:
            return
            
        # Trocar para nova animação
        self.current_animations[entity_id] = action
        self.animations[entity_id][action].reset()
        
    def update(self, dt: float):
        """
        Atualiza todas as animações ativas.
        
        Args:
            dt: Delta time em segundos
        """
        for entity_id, current_action in self.current_animations.items():
            if entity_id in self.animations and current_action in self.animations[entity_id]:
                animation = self.animations[entity_id][current_action]
                animation.update(dt)
                
                # Se animação não-loop terminou, voltar para idle
                if animation.is_finished() and current_action != "idle":
                    if "idle" in self.animations[entity_id]:
                        self.play_animation(entity_id, "idle")
                        
    def get_current_frame(self, entity_id: str) -> Optional[pygame.Surface]:
        """
        Retorna o frame atual de uma entidade.
        
        Args:
            entity_id: ID da entidade
            
        Returns:
            Surface do frame atual ou None
        """
        if entity_id not in self.current_animations:
            return None
            
        current_action = self.current_animations[entity_id]
        if entity_id not in self.animations or current_action not in self.animations[entity_id]:
            return None
            
        return self.animations[entity_id][current_action].current()


# Instância global do gerenciador de animações
animation_manager = AnimationManager()
