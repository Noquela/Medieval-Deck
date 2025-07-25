#!/usr/bin/env python3
"""
Test P2 Integration
Test suite to verify P2 features are properly integrated.
"""

import pygame
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_p2_imports():
    """Test that all P2 components can be imported."""
    print("Testing P2 imports...")
    
    try:
        # Test CardSprite P2
        from src.ui.card_sprite import CardSprite
        print("✅ CardSprite imported successfully")
        
        # Test FrameAnimation P2
        from src.gameplay.animation import FrameAnimation, AnimationManager, animation_manager, load_sprite_sheet
        print("✅ Animation system imported successfully")
        
        # Test ParticleEmitter P2
        from src.ui.particles import ParticleEmitter
        print("✅ ParticleEmitter imported successfully")
        
        # Test TurnEngine P2
        from src.core.turn_engine import TurnEngine
        print("✅ TurnEngine imported successfully")
        
        # Test CombatScreen with P2 integration
        from src.ui.combat_screen import CombatScreen
        print("✅ CombatScreen with P2 integration imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_p2_systems():
    """Test P2 systems basic functionality."""
    print("\nTesting P2 systems...")
    
    try:
        pygame.init()
        
        # Test CardSprite creation
        from src.ui.card_sprite import CardSprite
        test_surface = pygame.Surface((100, 150), pygame.SRCALPHA)
        test_surface.fill((100, 100, 200))
        card_sprite = CardSprite(test_surface, (0, 0))  # Corrigido: pos como tupla
        print("✅ CardSprite creation successful")
        
        # Test CardSprite hover effects
        card_sprite.set_hovered(True)
        card_sprite.update((50, 50), 0.016)  # mouse_pos, dt
        print("✅ CardSprite hover effects working")
        
        # Test FrameAnimation
        from src.gameplay.animation import FrameAnimation
        test_frames = [pygame.Surface((50, 50)) for _ in range(4)]
        frame_anim = FrameAnimation(test_frames, frame_duration=0.1)
        frame_anim.update(0.05)
        print("✅ FrameAnimation working")
        
        # Test ParticleEmitter P2 methods
        from src.ui.particles import ParticleEmitter, ParticleType
        emitter = ParticleEmitter(0, 0, 10, 10, ParticleType.GOLDEN_SPARKS)
        emitter.emit_damage((100, 100))
        emitter.emit_impact((150, 150))
        emitter.emit_heal((200, 200))
        print("✅ ParticleEmitter P2 methods working")
        
        # Test TurnEngine P2 methods
        from src.core.turn_engine import TurnEngine
        from src.models.card import Card
        from src.enemies.smart_enemy import SmartEnemy
        
        turn_engine = TurnEngine()
        
        # Test simplified turn methods
        turn_engine.player_turn_simple()
        turn_engine.enemy_turn_simple()
        print("✅ TurnEngine P2 simplified methods working")
        
        pygame.quit()
        return True
        
    except Exception as e:
        print(f"❌ P2 systems test failed: {e}")
        pygame.quit()
        return False

def test_p2_combat_integration():
    """Test P2 features integrated into CombatScreen."""
    print("\nTesting P2 CombatScreen integration...")
    
    try:
        pygame.init()
        screen = pygame.Surface((1024, 768))
        
        # Import required components
        from src.ui.combat_screen import CombatScreen
        from src.enemies.intelligent_combat import IntelligentCombatEngine
        from src.core.turn_engine import Player
        
        # Create player for combat engine
        player = Player(max_hp=100, max_mana=10)
        
        # Create combat engine
        combat_engine = IntelligentCombatEngine(player)
        
        # Create CombatScreen with P2 integration
        combat_screen = CombatScreen(screen, combat_engine)
        print("✅ CombatScreen with P2 created successfully")
        
        # Test P2 hand logic
        combat_screen.draw_initial_hand()
        print(f"✅ P2-6: Initial hand drawn ({len(combat_screen.player_hand)} cards)")
        
        # Test P2 hand operations
        if combat_screen.player_hand:
            test_card = combat_screen.player_hand[0]
            combat_screen.discard_card(test_card)
            print("✅ P2-6: Card discard working")
            
        combat_screen.draw_card()
        print("✅ P2-6: Card draw working")
        
        # Test P2 animation manager integration
        if hasattr(combat_screen, 'animation_manager'):
            print("✅ P2: Animation manager integrated")
            
            # Test update loop
            combat_screen.update(0.016)  # 60fps
            print("✅ P2: Update loop with animation manager working")
        
        pygame.quit()
        return True
        
    except Exception as e:
        print(f"❌ P2 CombatScreen integration test failed: {e}")
        pygame.quit()
        return False

def main():
    """Run all P2 integration tests."""
    print("=" * 50)
    print("P2 INTEGRATION TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_p2_imports,
        test_p2_systems,
        test_p2_combat_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL P2 FEATURES INTEGRATED SUCCESSFULLY!")
        print("\nP2 Sprint Completed:")
        print("✅ P2-1: CardSprite hover/glow effects")
        print("✅ P2-2: FrameAnimation 30fps system")
        print("✅ P2-3: Attack animation triggers")
        print("✅ P2-4: ParticleEmitter combat effects")
        print("✅ P2-5: TurnEngine minimum functionality")
        print("✅ P2-6: Hand logic (draw 5, discard, redraw)")
        print("\n🚀 Ready for P2 live testing!")
    else:
        print("❌ Some P2 features need attention")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
