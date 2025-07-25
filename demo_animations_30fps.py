#!/usr/bin/env python3
"""
Medieval Deck - Demo de Animações 30fps

Script de demonstração que mostra como o sistema de animações funciona.
Execute para ver personagens animados em tempo real.
"""

import sys
import pygame
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gameplay.animation import animation_manager
from utils.sprite_loader import load_character_animations

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Demo das animações 30fps."""
    
    # Inicializar pygame
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Medieval Deck - Demo Animações 30fps")
    clock = pygame.time.Clock()
    
    # Carregar animações
    characters = ["knight", "goblin", "orc", "skeleton", "mage"]
    loaded_chars = []
    
    for char in characters:
        if load_character_animations(char):
            loaded_chars.append(char)
            animation_manager.play_animation(char, "idle")
            logger.info(f"✅ {char} carregado")
        else:
            logger.warning(f"❌ {char} não encontrado")
    
    if not loaded_chars:
        logger.error("Nenhuma animação carregada! Execute scripts/generate_sprite_sheets.py primeiro")
        return
    
    # Estado da demo
    current_action = "idle"
    actions = ["idle", "attack", "cast", "hurt"]
    action_index = 0
    
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    logger.info("🎮 Demo iniciada! Use ESPAÇO para trocar ação, ESC para sair")
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Trocar ação
                    action_index = (action_index + 1) % len(actions)
                    current_action = actions[action_index]
                    
                    # Aplicar nova ação a todos os personagens
                    for char in loaded_chars:
                        animation_manager.play_animation(char, current_action, force_restart=True)
                    
                    logger.info(f"🎬 Ação: {current_action}")
        
        # Atualizar animações
        animation_manager.update(dt)
        
        # Desenhar
        screen.fill((20, 25, 30))  # Fundo escuro
        
        # Título
        title_text = font.render("Medieval Deck - Animações 30fps", True, (255, 255, 255))
        screen.blit(title_text, (50, 30))
        
        # Ação atual
        action_text = font.render(f"Ação: {current_action.upper()}", True, (255, 215, 0))
        screen.blit(action_text, (50, 80))
        
        # Instruções
        inst_text = small_font.render("ESPAÇO: Trocar ação | ESC: Sair", True, (200, 200, 200))
        screen.blit(inst_text, (50, 120))
        
        # Desenhar personagens em linha
        y_pos = 200
        x_spacing = screen.get_width() // (len(loaded_chars) + 1)
        
        for i, char in enumerate(loaded_chars):
            x_pos = x_spacing * (i + 1)
            
            # Frame atual da animação
            frame = animation_manager.get_current_frame(char)
            if frame:
                # Escalar para tamanho apropriado
                max_height = 300
                if frame.get_height() > max_height:
                    ratio = max_height / frame.get_height()
                    new_size = (int(frame.get_width() * ratio), max_height)
                    frame = pygame.transform.smoothscale(frame, new_size)
                
                # Posicionar e desenhar
                frame_rect = frame.get_rect(centerx=x_pos, bottom=y_pos + max_height)
                screen.blit(frame, frame_rect)
                
                # Nome do personagem
                name_text = small_font.render(char.title(), True, (255, 255, 255))
                name_rect = name_text.get_rect(centerx=x_pos, top=frame_rect.bottom + 10)
                screen.blit(name_text, name_rect)
        
        # FPS counter
        fps_text = small_font.render(f"FPS: {int(clock.get_fps())}", True, (100, 255, 100))
        screen.blit(fps_text, (screen.get_width() - 100, 30))
        
        pygame.display.flip()
    
    pygame.quit()
    logger.info("Demo finalizada!")


if __name__ == "__main__":
    main()
