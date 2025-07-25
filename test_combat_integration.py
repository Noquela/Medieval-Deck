#!/usr/bin/env python3
"""
Test Combat Integration

Teste simples para verificar se a integração da tela de combate está funcionando.
"""

import pygame
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.utils.config import Config
from src.game.engine import GameEngine
from src.game.ui import GameUI

def main():
    """Test combat integration."""
    try:
        # Initialize pygame
        pygame.init()
        
        # Initialize configuration
        config = Config()
        
        # Initialize game engine
        game_engine = GameEngine(config=config)
        
        # Initialize UI
        game_ui = GameUI(
            config=config,
            game_engine=game_engine,
            asset_generator=None
        )
        
        print("✅ GameUI initialized successfully!")
        print(f"Current state: {game_ui.current_state}")
        print(f"Available screens: {list(game_ui.screens.keys())}")
        
        # Test combat screen initialization
        game_ui._initialize_combat_screen("knight")
        print("✅ Combat screen initialized successfully!")
        
        # Test transition to combat
        print("Testing transition to combat...")
        game_ui._transition_to_state(game_ui.UIState.COMBAT)
        print(f"Current state after transition: {game_ui.current_state}")
        
        print("🎉 All tests passed! Combat integration is working.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        pygame.quit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
