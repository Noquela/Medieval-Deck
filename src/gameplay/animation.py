"""
Medieval Deck - Sistema de Animação de Sprite Sheets

Geração automática de animações 30fps com IA e reprodução fluida.
Enhanced for P2 Sprint with precise timing and state management.
"""

import pygame
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class FrameAnimation:
    """
    Reproduz animação de sprite sheet a 30 fps com controle de loop.
    Enhanced for P2 with precise timing and state management.
    """
    
    def __init__(self, frames: List[pygame.Surface], fps: int = 30, loop: bool = True):
        """
        Inicializa animação de frames.
        
        Args:
            frames: Lista de surfaces dos quadros
            fps: Frames por segundo
            loop: Se deve repetir a animação
        """
        if not frames:
            raise ValueError("Frames list cannot be empty")
            
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.timer = 0.0
        self.current_frame = 0
        self.finished = False
        self.paused = False
        
        # P2 enhancements
        self.frame_duration = 1.0 / self.fps
        self.total_duration = len(self.frames) * self.frame_duration
        
    def update(self, dt: float):
        """
        Atualiza o timer e frame atual.
        
        Args:
            dt: Delta time em segundos
        """
        if self.finished and not self.loop or self.paused:
            return
            
        self.timer += dt
        
        if self.loop:
            # Loop infinito
            self.timer %= self.total_duration
            self.current_frame = min(int(self.timer * self.fps), len(self.frames) - 1)
        else:
            # Executa uma vez
            if self.timer >= self.total_duration:
                self.current_frame = len(self.frames) - 1
                self.finished = True
            else:
                self.current_frame = min(int(self.timer * self.fps), len(self.frames) - 1)
                
    def current(self) -> pygame.Surface:
        """Retorna o frame atual da animação."""
        if not self.frames:
            raise RuntimeError("No frames available")
        return self.frames[self.current_frame]
        
    def reset(self):
        """Reinicia a animação do início."""
        self.timer = 0.0
        self.current_frame = 0
        self.finished = False
        self.paused = False
        
    def pause(self):
        """Pausa a animação."""
        self.paused = True
        
    def resume(self):
        """Resume a animação pausada."""
        self.paused = False
        
    def is_finished(self) -> bool:
        """Verifica se a animação terminou (para animações não-loop)."""
        return self.finished
        
    def get_progress(self) -> float:
        """Retorna o progresso da animação (0.0 a 1.0)."""
        if self.total_duration == 0:
            return 1.0
        return min(self.timer / self.total_duration, 1.0)
        
    def set_frame(self, frame_index: int):
        """Define um frame específico manualmente."""
        if 0 <= frame_index < len(self.frames):
            self.current_frame = frame_index
            self.timer = frame_index * self.frame_duration


class AnimationManager:
    """
    Gerencia múltiplas animações por entidade.
    Enhanced for P2 with better state management.
    """
    
    def __init__(self):
        self.animations: Dict[str, Dict[str, FrameAnimation]] = {}
        self.current_animations: Dict[str, str] = {}
        self.pending_transitions: Dict[str, str] = {}
        
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
        if entity_id not in self.animations:
            logger.warning(f"Entity {entity_id} not found in animations")
            return
            
        if action not in self.animations[entity_id]:
            logger.warning(f"Animation {action} not found for entity {entity_id}")
            return
            
        current_action = self.current_animations.get(entity_id)
        
        if current_action != action or force_restart:
            self.current_animations[entity_id] = action
            self.animations[entity_id][action].reset()
            
    def transition_to(self, entity_id: str, action: str, after_current: bool = False):
        """
        Transição suave para outra animação.
        
        Args:
            entity_id: ID da entidade
            action: Animação de destino
            after_current: Se deve esperar a animação atual terminar
        """
        if after_current:
            self.pending_transitions[entity_id] = action
        else:
            self.play_animation(entity_id, action)
            
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
                
                # Check for pending transitions
                if (entity_id in self.pending_transitions and 
                    animation.is_finished() and not animation.loop):
                    
                    next_action = self.pending_transitions.pop(entity_id)
                    self.play_animation(entity_id, next_action)
                    
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
        
        if (entity_id in self.animations and 
            current_action in self.animations[entity_id]):
            return self.animations[entity_id][current_action].current()
            
        return None
        
    def is_animation_finished(self, entity_id: str) -> bool:
        """Verifica se a animação atual da entidade terminou."""
        if entity_id not in self.current_animations:
            return True
            
        current_action = self.current_animations[entity_id]
        
        if (entity_id in self.animations and 
            current_action in self.animations[entity_id]):
            return self.animations[entity_id][current_action].is_finished()
            
        return True
        
    def get_current_action(self, entity_id: str) -> Optional[str]:
        """Retorna a ação atual da entidade."""
        return self.current_animations.get(entity_id)


# Global animation manager instance
animation_manager = AnimationManager()


def load_sprite_sheet(image_path: str, frame_count: int, frame_width: int = None, 
                     frame_height: int = None) -> List[pygame.Surface]:
    """
    Carrega uma sprite sheet em frames individuais.
    
    Args:
        image_path: Caminho para a imagem
        frame_count: Número de frames na sheet
        frame_width: Largura de cada frame (auto se None)
        frame_height: Altura de cada frame (auto se None)
        
    Returns:
        Lista de surfaces dos frames
    """
    try:
        sheet = pygame.image.load(image_path).convert_alpha()
        
        if frame_width is None:
            frame_width = sheet.get_width() // frame_count
        if frame_height is None:
            frame_height = sheet.get_height()
            
        frames = []
        for i in range(frame_count):
            frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
            frame = sheet.subsurface(frame_rect).copy()
            frames.append(frame)
            
        logger.info(f"Loaded {len(frames)} frames from {image_path}")
        return frames
        
    except Exception as e:
        logger.error(f"Failed to load sprite sheet {image_path}: {e}")
        # Return dummy frame
        dummy_frame = pygame.Surface((frame_width or 64, frame_height or 64), pygame.SRCALPHA)
        dummy_frame.fill((255, 0, 255, 128))  # Magenta placeholder
        return [dummy_frame] * frame_count


def load_character_animations(character_id: str) -> bool:
    """
    Carrega todas as animações de um personagem.
    
    Args:
        character_id: ID do personagem (knight, goblin, etc.)
        
    Returns:
        True se as animações foram carregadas com sucesso
    """
    try:
        # Definir ações padrão para personagens
        actions = ["idle", "attack", "hurt", "death"]
        
        # Criar frames dummy para teste (será substituído por assets reais)
        frames_per_action = 4
        frame_size = (64, 64)
        
        for action in actions:
            frames = []
            for i in range(frames_per_action):
                frame = pygame.Surface(frame_size, pygame.SRCALPHA)
                
                # Cores diferentes para cada ação (placeholder visual)
                color = {
                    "idle": (100, 100, 200),
                    "attack": (200, 100, 100),
                    "hurt": (200, 200, 100),
                    "death": (100, 100, 100)
                }.get(action, (150, 150, 150))
                
                frame.fill(color)
                frames.append(frame)
            
            # Criar animação
            frame_duration = 0.15 if action == "idle" else 0.1
            loop = action == "idle"
            
            animation = FrameAnimation(frames, frame_duration, loop)
            animation_manager.add_animation(character_id, action, animation)
            
        logger.info(f"Loaded animations for {character_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load character animations for {character_id}: {e}")
        return False
