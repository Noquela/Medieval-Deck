#!/usr/bin/env python3
"""
Minimal Combat Test

Teste mínimo para identificar o problema.
"""

import pygame
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def test_imports():
    """Test imports only."""
    try:
        print("Testing imports...")
        
        from src.utils.config import Config
        print("✅ Config imported")
        
        from src.game.engine import GameEngine
        print("✅ GameEngine imported")
        
        from src.game.ui import GameUI
        print("✅ GameUI imported")
        
        from src.core.turn_engine import Player
        print("✅ Player imported")
        
        from src.enemies.intelligent_combat import IntelligentCombatEngine
        print("✅ IntelligentCombatEngine imported")
        
        from src.ui.combat_screen import CombatScreen
        print("✅ CombatScreen imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_init():
    """Test basic initialization without pygame display."""
    try:
        print("\nTesting basic initialization...")
        
        from src.utils.config import Config
        config = Config()
        print("✅ Config created")
        
        from src.core.turn_engine import Player
        player = Player()
        print("✅ Player created")
        
        from src.enemies.intelligent_combat import IntelligentCombatEngine
        combat_engine = IntelligentCombatEngine(player=player)
        print("✅ IntelligentCombatEngine created")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic init failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run minimal tests."""
    print("🧪 Running minimal combat tests...")
    
    # Test 1: Imports
    if not test_imports():
        return False
    
    # Test 2: Basic initialization
    if not test_basic_init():
        return False
        
    print("\n🎉 All minimal tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
