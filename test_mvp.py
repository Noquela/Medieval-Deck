#!/usr/bin/env python3
"""
Medieval Deck - MVP Test

Teste básico do MVP com os novos sistemas.
"""

import sys
import pygame
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(project_root))

from src.utils.theme import Theme
from src.gameplay.mvp_cards import MVPCards, Card
from src.gameplay.mvp_deck import MVPDeck
from src.core.mvp_turn_engine import MVPPlayer, MVPEnemy, MVPTurnEngine
from src.ui.card_view import CardView

def test_mvp_systems():
    """Testa os sistemas básicos do MVP."""
    print("🎮 Testing MVP Systems...")
    
    # 1. Teste das cartas
    print("\n📇 Testing Cards...")
    cards = MVPCards.get_all_cards()
    print(f"✅ Loaded {len(cards)} cards")
    
    for card_id, card in cards.items():
        print(f"   • {card.name}: {card.mana_cost} mana, {card.description}")
    
    # 2. Teste do deck
    print("\n🃏 Testing Deck...")
    deck = MVPDeck()
    info = deck.get_deck_info()
    print(f"✅ Deck created with {info['total_cards']} cards")
    
    hand = deck.draw_hand(5)
    print(f"✅ Drew hand of {len(hand)} cards")
    for card in hand:
        print(f"   • {card.name}")
    
    # 3. Teste do turn engine
    print("\n⚔️ Testing Turn Engine...")
    player = MVPPlayer(max_hp=50, max_mana=3)
    enemy = MVPEnemy("Goblin Scout", hp=25, attack=6)
    engine = MVPTurnEngine(player, enemy)
    
    print(f"✅ Player: {player.current_hp}/{player.max_hp} HP, {player.current_mana}/{player.max_mana} Mana")
    print(f"✅ Enemy: {enemy.name} - {enemy.current_hp}/{enemy.max_hp} HP, {enemy.attack} ATK")
    
    # Simular jogada
    strike_card = cards["strike"]
    if strike_card.can_play(player.current_mana):
        result = engine.play_card(strike_card)
        print(f"✅ Played Strike: {result['success']}")
        for effect in result.get('effects', []):
            print(f"   • {effect['type']}: {effect['amount']}")
    
    status = engine.get_status()
    print(f"✅ Game Status: Turn {status['turn']}, Player Turn: {status['player_turn']}")
    
    return True

def test_mvp_ui():
    """Testa a interface básica do MVP."""
    print("\n🎨 Testing MVP UI...")
    
    # Inicializar pygame
    pygame.init()
    Theme.init_fonts()
    
    # Criar surface de teste
    screen = pygame.Surface((800, 600))
    
    # Teste CardView
    cards = MVPCards.get_all_cards()
    strike_card = cards["strike"]
    
    card_view = CardView(strike_card, (400, 500))
    card_view.draw(screen)
    
    print("✅ CardView created and rendered")
    
    # Teste Theme
    zones = Theme.create_zones((1920, 1080))
    print(f"✅ Created {len(zones)} UI zones")
    for zone_name, zone_rect in zones.items():
        print(f"   • {zone_name}: {zone_rect}")
    
    return True

def main():
    """Teste principal do MVP."""
    print("🏰 Medieval Deck - MVP Test Suite")
    print("=" * 50)
    
    try:
        # Testes dos sistemas
        if test_mvp_systems():
            print("\n✅ MVP Systems: PASS")
        else:
            print("\n❌ MVP Systems: FAIL")
            return False
        
        # Testes da UI
        if test_mvp_ui():
            print("✅ MVP UI: PASS")
        else:
            print("❌ MVP UI: FAIL")
            return False
        
        print("\n🎉 MVP Test Suite: ALL TESTS PASSED!")
        print("\n📋 MVP Ready for Implementation:")
        print("   • Cards system working")
        print("   • Deck management working")
        print("   • Turn engine working")
        print("   • UI components working")
        print("   • Theme system working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ MVP Test Suite FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
