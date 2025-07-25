"""
Sistema de animações avançadas para Medieval Deck.

Implementa tweening, easing e animações de propriedades para criar
transições suaves e cinematográficas na interface.
"""

import pygame
import math
import time
from typing import Dict, Any, Callable, Optional, Tuple
from enum import Enum


class EasingType(Enum):
    """Tipos de curvas de easing para animações."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_IN_QUAD = "ease_in_quad"
    EASE_OUT_QUAD = "ease_out_quad"
    EASE_IN_OUT_QUAD = "ease_in_out_quad"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    BOUNCE_OUT = "bounce_out"
    ELASTIC_OUT = "elastic_out"


class Easing:
    """Funções de easing para diferentes tipos de animação."""
    
    @staticmethod
    def linear(t: float) -> float:
        """Interpolação linear."""
        return t
    
    @staticmethod
    def ease_in(t: float) -> float:
        """Aceleração suave no início."""
        return t * t
    
    @staticmethod
    def ease_out(t: float) -> float:
        """Desaceleração suave no final."""
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_out(t: float) -> float:
        """Aceleração no início, desaceleração no final."""
        if t < 0.5:
            return 2 * t * t
        return 1 - pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Aceleração quadrática."""
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Desaceleração quadrática."""
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Combinação quadrática."""
        if t < 0.5:
            return 2 * t * t
        return 1 - pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Aceleração cúbica."""
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Desaceleração cúbica."""
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Combinação cúbica."""
        if t < 0.5:
            return 4 * t * t * t
        return 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def bounce_out(t: float) -> float:
        """Efeito de quique no final."""
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375
    
    @staticmethod
    def elastic_out(t: float) -> float:
        """Efeito elástico no final."""
        c4 = (2 * math.pi) / 3
        
        if t == 0:
            return 0
        elif t == 1:
            return 1
        else:
            return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
    
    @classmethod
    def get_function(cls, easing_type: EasingType) -> Callable[[float], float]:
        """Retorna função de easing baseada no tipo."""
        mapping = {
            EasingType.LINEAR: cls.linear,
            EasingType.EASE_IN: cls.ease_in,
            EasingType.EASE_OUT: cls.ease_out,
            EasingType.EASE_IN_OUT: cls.ease_in_out,
            EasingType.EASE_IN_QUAD: cls.ease_in_quad,
            EasingType.EASE_OUT_QUAD: cls.ease_out_quad,
            EasingType.EASE_IN_OUT_QUAD: cls.ease_in_out_quad,
            EasingType.EASE_IN_CUBIC: cls.ease_in_cubic,
            EasingType.EASE_OUT_CUBIC: cls.ease_out_cubic,
            EasingType.EASE_IN_OUT_CUBIC: cls.ease_in_out_cubic,
            EasingType.BOUNCE_OUT: cls.bounce_out,
            EasingType.ELASTIC_OUT: cls.elastic_out,
        }
        return mapping.get(easing_type, cls.linear)


class Animation:
    """Representa uma animação de propriedade."""
    
    def __init__(self, 
                 target: Any,
                 property_name: str,
                 start_value: Any,
                 end_value: Any,
                 duration: float,
                 easing: EasingType = EasingType.EASE_OUT,
                 delay: float = 0.0,
                 on_complete: Optional[Callable] = None):
        """
        Inicializa animação.
        
        Args:
            target: Objeto a animar
            property_name: Nome da propriedade a animar
            start_value: Valor inicial
            end_value: Valor final
            duration: Duração em segundos
            easing: Tipo de easing
            delay: Atraso antes de iniciar
            on_complete: Callback ao completar
        """
        self.target = target
        self.property_name = property_name
        self.start_value = start_value
        self.end_value = end_value
        self.duration = duration
        self.easing_func = Easing.get_function(easing)
        self.delay = delay
        self.on_complete = on_complete
        
        self.start_time = time.time() + delay
        self.is_complete = False
        
        # Suporte para diferentes tipos de valores
        self.is_tuple = isinstance(start_value, (tuple, list))
        self.is_color = (isinstance(start_value, (tuple, list)) and 
                        len(start_value) in [3, 4] and 
                        all(isinstance(x, int) for x in start_value))
    
    def update(self) -> bool:
        """
        Atualiza animação.
        
        Returns:
            True se a animação ainda está rodando
        """
        if self.is_complete:
            return False
        
        current_time = time.time()
        if current_time < self.start_time:
            return True  # Ainda no delay
        
        elapsed = current_time - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # Aplica easing
        eased_progress = self.easing_func(progress)
        
        # Interpola valor
        if self.is_tuple:
            # Interpola tuplas/listas
            current_value = []
            for i in range(len(self.start_value)):
                start = self.start_value[i]
                end = self.end_value[i]
                current = start + (end - start) * eased_progress
                current_value.append(int(current) if self.is_color else current)
            
            if isinstance(self.start_value, tuple):
                current_value = tuple(current_value)
        else:
            # Interpola valores simples
            current_value = (self.start_value + 
                           (self.end_value - self.start_value) * eased_progress)
        
        # Define valor no objeto
        setattr(self.target, self.property_name, current_value)
        
        # Verifica se completou
        if progress >= 1.0:
            self.is_complete = True
            if self.on_complete:
                self.on_complete()
            return False
        
        return True


class AnimationManager:
    """Gerenciador global de animações."""
    
    def __init__(self):
        self.animations: Dict[str, Animation] = {}
        self.next_id = 0
    
    def animate(self,
                target: Any,
                property_name: str,
                end_value: Any,
                duration: float,
                easing: EasingType = EasingType.EASE_OUT,
                delay: float = 0.0,
                animation_id: Optional[str] = None,
                on_complete: Optional[Callable] = None) -> str:
        """
        Inicia nova animação.
        
        Args:
            target: Objeto a animar
            property_name: Propriedade a animar
            end_value: Valor final
            duration: Duração em segundos
            easing: Tipo de easing
            delay: Atraso antes de iniciar
            animation_id: ID personalizado (opcional)
            on_complete: Callback ao completar
        
        Returns:
            ID da animação
        """
        # Obtém valor inicial atual
        start_value = getattr(target, property_name)
        
        # Gera ID se não fornecido
        if animation_id is None:
            animation_id = f"anim_{self.next_id}"
            self.next_id += 1
        
        # Cancela animação existente com mesmo ID
        if animation_id in self.animations:
            del self.animations[animation_id]
        
        # Cria nova animação
        animation = Animation(
            target=target,
            property_name=property_name,
            start_value=start_value,
            end_value=end_value,
            duration=duration,
            easing=easing,
            delay=delay,
            on_complete=on_complete
        )
        
        self.animations[animation_id] = animation
        return animation_id
    
    def stop_animation(self, animation_id: str):
        """Para animação específica."""
        if animation_id in self.animations:
            del self.animations[animation_id]
    
    def stop_all_animations(self):
        """Para todas as animações."""
        self.animations.clear()
    
    def update(self):
        """Atualiza todas as animações ativas."""
        completed_animations = []
        
        # Usar list() para criar uma cópia e evitar "dictionary changed size during iteration"
        for anim_id, animation in list(self.animations.items()):
            if not animation.update():
                completed_animations.append(anim_id)
        
        # Remove animações completadas
        for anim_id in completed_animations:
            if anim_id in self.animations:  # Verificação extra de segurança
                del self.animations[anim_id]
    
    def is_animating(self, target: Any, property_name: Optional[str] = None) -> bool:
        """
        Verifica se objeto/propriedade está sendo animado.
        
        Args:
            target: Objeto a verificar
            property_name: Propriedade específica (opcional)
        
        Returns:
            True se está sendo animado
        """
        for animation in self.animations.values():
            if animation.target == target:
                if property_name is None or animation.property_name == property_name:
                    return True
        return False


# Instância global do gerenciador
animation_manager = AnimationManager()


# Funções de conveniência para uso fácil
def animate(target: Any, **kwargs) -> str:
    """
    Anima propriedade de objeto.
    
    Exemplo:
        animate(button, scale=1.1, duration=0.2, easing=EasingType.EASE_OUT)
    """
    if len(kwargs) != 1:
        raise ValueError("animate() deve receber exatamente uma propriedade para animar")
    
    property_name = list(kwargs.keys())[0]
    end_value = list(kwargs.values())[0]
    
    return animation_manager.animate(
        target=target,
        property_name=property_name,
        end_value=end_value,
        duration=kwargs.get('duration', 0.3),
        easing=kwargs.get('easing', EasingType.EASE_OUT),
        delay=kwargs.get('delay', 0.0),
        animation_id=kwargs.get('animation_id'),
        on_complete=kwargs.get('on_complete')
    )


def animate_to(target: Any, 
               property_name: str,
               end_value: Any,
               duration: float = 0.3,
               easing: EasingType = EasingType.EASE_OUT,
               delay: float = 0.0,
               on_complete: Optional[Callable] = None) -> str:
    """Versão explícita da função animate."""
    return animation_manager.animate(
        target=target,
        property_name=property_name,
        end_value=end_value,
        duration=duration,
        easing=easing,
        delay=delay,
        on_complete=on_complete
    )


def fade_in(target: Any, duration: float = 0.3) -> str:
    """Animação de fade in."""
    return animate_to(target, 'alpha', 255, duration, EasingType.EASE_OUT)


def fade_out(target: Any, duration: float = 0.3) -> str:
    """Animação de fade out."""
    return animate_to(target, 'alpha', 0, duration, EasingType.EASE_IN)


def scale_to(target: Any, scale: float, duration: float = 0.2) -> str:
    """Animação de escala."""
    return animate_to(target, 'scale', scale, duration, EasingType.EASE_OUT)


def slide_in_from_left(target: Any, final_x: float, duration: float = 0.4) -> str:
    """Desliza elemento da esquerda."""
    # Assume que o objeto tem uma propriedade x
    return animate_to(target, 'x', final_x, duration, EasingType.EASE_OUT_CUBIC)


def slide_in_from_bottom(target: Any, final_y: float, duration: float = 0.4) -> str:
    """Desliza elemento de baixo."""
    return animate_to(target, 'y', final_y, duration, EasingType.EASE_OUT_CUBIC)
