"""
Medieval Deck - Gerador de Sprite Sheets com IA

Sistema automático para gerar animações de personagens usando Stable Diffusion XL.
Produz sprite sheets horizontais prontos para animação 30fps.
"""

import pygame
import logging
from pathlib import Path
from typing import List, Optional, Dict
import hashlib

from ..models.sdxl_pipeline import SDXLPipeline

logger = logging.getLogger(__name__)


class SpriteSheetGenerator:
    """
    Gerador automático de sprite sheets para animações.
    """
    
    def __init__(self, pipeline: SDXLPipeline):
        """
        Inicializa o gerador de sprite sheets.
        
        Args:
            pipeline: Pipeline SDXL configurado
        """
        self.pipeline = pipeline
        self.output_dir = Path("assets/sprite_sheets")
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_sprite_sheet(self, char_id: str, action: str, base_prompt: str, 
                            n_frames: int = 10, width: int = 512, height: int = 512) -> Optional[str]:
        """
        Gera sprite sheet com múltiplos frames de uma ação.
        
        Args:
            char_id: ID do personagem (knight, goblin, etc)
            action: Ação (idle, attack, cast, death)
            base_prompt: Prompt base para a IA
            n_frames: Número de frames a gerar
            width: Largura de cada frame
            height: Altura de cada frame
            
        Returns:
            Caminho do sprite sheet gerado ou None se falhou
        """
        logger.info(f"Gerando sprite sheet: {char_id}_{action} ({n_frames} frames)")
        
        # Gerar seed consistente baseado no char_id
        seed = int(hashlib.md5(char_id.encode()).hexdigest()[:8], 16) % (2**32)
        
        try:
            # Gerar todos os frames
            frames = []
            for i in range(n_frames):
                # Prompt específico para cada frame
                frame_prompt = self._create_frame_prompt(base_prompt, action, i, n_frames)
                
                logger.debug(f"Gerando frame {i+1}/{n_frames}: {frame_prompt}")
                
                # Usar mesmo seed com pequena variação para consistência
                frame_seed = seed + i
                
                # Gerar imagem
                image = self.pipeline.generate_image(
                    prompt=frame_prompt,
                    width=width,
                    height=height,
                    seed=frame_seed,
                    num_inference_steps=80,
                    guidance_scale=8.5
                )
                
                if image:
                    # Converter PIL para pygame Surface
                    mode = image.mode
                    size = image.size
                    data = image.tobytes()
                    
                    if mode == "RGBA":
                        frame_surface = pygame.image.fromstring(data, size, mode)
                    else:
                        # Converter para RGBA se necessário
                        image = image.convert("RGBA")
                        data = image.tobytes()
                        frame_surface = pygame.image.fromstring(data, size, "RGBA")
                    
                    frames.append(frame_surface)
                else:
                    logger.error(f"Falha ao gerar frame {i} para {char_id}_{action}")
                    return None
                    
            # Concatenar frames horizontalmente
            sheet_width = width * n_frames
            sheet_height = height
            sprite_sheet = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
            
            for idx, frame in enumerate(frames):
                x_pos = idx * width
                sprite_sheet.blit(frame, (x_pos, 0))
                
            # Salvar sprite sheet
            output_path = self.output_dir / f"{char_id}_{action}_sheet.png"
            pygame.image.save(sprite_sheet, str(output_path))
            
            logger.info(f"✅ Sprite sheet salvo: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Erro ao gerar sprite sheet {char_id}_{action}: {e}")
            return None
            
    def _create_frame_prompt(self, base_prompt: str, action: str, frame_idx: int, total_frames: int) -> str:
        """
        Cria prompt específico para um frame da animação.
        
        Args:
            base_prompt: Prompt base do personagem
            action: Ação sendo animada
            frame_idx: Índice do frame (0-based)
            total_frames: Total de frames na animação
            
        Returns:
            Prompt completo para o frame
        """
        # Calcular progresso da animação (0.0 a 1.0)
        progress = frame_idx / max(1, total_frames - 1)
        
        # Descritores específicos por ação e progresso
        action_descriptors = self._get_action_descriptors(action, progress)
        
        # Qualificadores visuais para consistência
        style_qualifiers = [
            "transparent background",
            "full body character",
            "high detail",
            "consistent art style",
            "medieval fantasy",
            "painterly style",
            "same character design",
            "consistent lighting",
            "stable diffusion xl",
            f"animation frame {frame_idx+1} of {total_frames}"
        ]
        
        # Montar prompt final
        full_prompt = f"{base_prompt}, {action_descriptors}, {', '.join(style_qualifiers)}"
        
        return full_prompt
        
    def _get_action_descriptors(self, action: str, progress: float) -> str:
        """
        Retorna descritores específicos da ação baseado no progresso.
        
        Args:
            action: Nome da ação
            progress: Progresso da animação (0.0-1.0)
            
        Returns:
            Descritor textual da pose
        """
        if action == "idle":
            # Idle: movimento sutil de respiração
            if progress < 0.5:
                return "standing pose, relaxed stance, breathing in"
            else:
                return "standing pose, relaxed stance, breathing out"
                
        elif action == "attack":
            # Attack: wind-up -> strike -> follow-through
            if progress < 0.3:
                return "raising weapon, preparing to strike, wind-up pose"
            elif progress < 0.6:
                return "mid-attack, weapon swinging, action pose"
            else:
                return "follow-through, weapon extended, completion pose"
                
        elif action == "cast":
            # Cast: gathering energy -> casting -> completion
            if progress < 0.4:
                return "gathering magical energy, hands glowing, preparation"
            elif progress < 0.7:
                return "casting spell, energy flowing, magical gestures"
            else:
                return "spell completion, energy released, finishing pose"
                
        elif action == "hurt":
            # Hurt: impact -> recoil -> recovery
            if progress < 0.3:
                return "taking damage, impact reaction, stumbling"
            elif progress < 0.7:
                return "recoiling from hit, defensive posture"
            else:
                return "recovering balance, defensive stance"
                
        elif action == "death":
            # Death: falling -> collapsed
            if progress < 0.5:
                return "falling down, collapsing, losing balance"
            else:
                return "on ground, defeated pose, motionless"
                
        else:
            # Ação genérica
            return f"{action} pose, dynamic movement"
            
    def generate_character_animations(self, char_id: str, base_prompt: str, 
                                    actions: List[str] = None) -> Dict[str, str]:
        """
        Gera sprite sheets para todas as animações de um personagem.
        
        Args:
            char_id: ID do personagem
            base_prompt: Descrição base do personagem
            actions: Lista de ações a gerar (default: idle, attack, cast, hurt)
            
        Returns:
            Dicionário {action: path} dos sprite sheets gerados
        """
        if actions is None:
            actions = ["idle", "attack", "cast", "hurt"]
            
        results = {}
        
        for action in actions:
            # Número de frames baseado na ação
            if action == "idle":
                n_frames = 8  # Loop mais curto para idle
            elif action in ["attack", "cast"]:
                n_frames = 12  # Mais frames para ações complexas
            else:
                n_frames = 10  # Padrão
                
            path = self.generate_sprite_sheet(
                char_id=char_id,
                action=action,
                base_prompt=base_prompt,
                n_frames=n_frames
            )
            
            if path:
                results[action] = path
                
        logger.info(f"Geradas {len(results)} animações para {char_id}")
        return results
