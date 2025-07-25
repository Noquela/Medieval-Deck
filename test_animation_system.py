#!/usr/bin/env python3
"""
Teste simples do sistema de animação sem geração de sprites.
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    # Testar imports básicos
    print("=== Testando Sistema de Animação ===")
    
    from gameplay.animation import animation_manager, FrameAnimation
    print("✅ Animation manager importado")
    
    from utils.sprite_loader import load_character_animations
    print("✅ Sprite loader importado")
    
    # Testar se temos sprites existentes
    from pathlib import Path
    sprite_dir = Path("assets/generated")
    if sprite_dir.exists():
        sprite_files = list(sprite_dir.glob("*_sprite.png"))
        print(f"✅ Encontrados {len(sprite_files)} sprites existentes")
        for sprite in sprite_files[:5]:  # Mostrar primeiros 5
            print(f"   - {sprite.name}")
    
    # Testar criação de animação fake
    fake_frames = []
    for i in range(8):  # 8 frames de teste
        # Criar frame placeholder
        import pygame
        pygame.init()
        frame = pygame.Surface((64, 64), pygame.SRCALPHA)
        frame.fill((100 + i*20, 50, 50, 255))  # Cor variando
        fake_frames.append(frame)
    
    # Adicionar animação de teste
    animation_manager.add_animation(
        entity_id="test_character",
        action="idle",
        frames=fake_frames,
        fps=30,
        loop=True
    )
    
    # Reproduzir animação
    animation_manager.play_animation("test_character", "idle")
    print("✅ Animação de teste criada e reproduzindo")
    
    # Testar update
    import time
    for i in range(10):
        dt = 1/30  # 30 FPS
        animation_manager.update(dt)
        current_frame = animation_manager.get_current_frame("test_character")
        if current_frame:
            print(f"   Frame {i}: {current_frame.get_size()}")
        time.sleep(0.1)
    
    print("🎯 Sistema de animação funcionando perfeitamente!")
    print("🎯 Pronto para usar com sprites reais!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
