"""
Medieval Deck - Demo do Sistema de Gameplay Completo

Demonstração da Fase 2 do roadmap:
- Sistema de cartas funcionando
- Deck management
- Integração com TurnEngine
- Gameplay completo

Execute: python demo_gameplay.py
"""

import sys
import logging
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.turn_engine import Player, Enemy
from src.gameplay.gameplay_engine import GameplayEngine, GameplayDemo
from src.gameplay.cards import CreatureCard, SpellCard, ArtifactCard, CreatureType, SpellType, ArtifactType
from src.gameplay.deck import DeckBuilder


def demo_card_creation():
    """Demonstra criação de cartas."""
    print("\n=== DEMO: Card Creation ===")
    
    # Criatura - Cavaleiro (Tank)
    knight = CreatureCard(
        "knight_01", "Brave Knight", cost=3, 
        description="A valiant knight with strong defense",
        attack=2, defense=5, creature_type=CreatureType.TANK,
        abilities=["taunt"]
    )
    print(f"Created: {knight}")
    
    # Criatura - Assassino (DPS)
    assassin = CreatureCard(
        "assassin_01", "Shadow Assassin", cost=2,
        description="Swift assassin with high attack",
        attack=4, defense=2, creature_type=CreatureType.DPS
    )
    print(f"Created: {assassin}")
    
    # Magia - Bola de Fogo
    fireball = SpellCard(
        "fireball_01", "Fireball", cost=3,
        description="Deals damage to all enemies",
        spell_type=SpellType.AOE, effect_value=3
    )
    print(f"Created: {fireball}")
    
    # Artefato - Poção
    potion = ArtifactCard(
        "health_potion", "Health Potion", cost=1,
        description="Restore health instantly",
        artifact_type=ArtifactType.CONSUMABLE
    )
    print(f"Created: {potion}")
    
    return [knight, assassin, fireball, potion]


def demo_deck_system():
    """Demonstra sistema de deck."""
    print("\n=== DEMO: Deck System ===")
    
    # Criar deck inicial
    deck = DeckBuilder.create_starter_deck("balanced")
    print(f"Created starter deck: {deck}")
    
    # Comprar mão inicial
    initial_hand = deck.draw(5)
    print(f"Drew initial hand of {len(initial_hand)} cards:")
    for card in initial_hand:
        print(f"  - {card}")
    
    # Mostrar cartas jogáveis (simulando jogador com 5 de mana)
    class MockPlayer:
        def __init__(self):
            self.mana = 5
            self.max_mana = 10
            self.hp = 30
            self.max_hp = 30
        
        def spend_mana(self, amount):
            if self.mana >= amount:
                self.mana -= amount
                return True
            return False
        
        def heal(self, amount):
            self.hp = min(self.max_hp, self.hp + amount)
    
    mock_player = MockPlayer()
    playable = deck.get_playable_cards(mock_player)
    print(f"\nPlayable cards with {mock_player.mana} mana:")
    for card in playable:
        print(f"  - {card}")
    
    return deck, mock_player


def demo_full_gameplay():
    """Demonstra gameplay completo."""
    print("\n=== DEMO: Full Gameplay ===")
    
    # Criar jogador e inimigos
    player = Player(max_hp=30, max_mana=10)
    player.name = "Brave Hero"  # Adicionar nome depois
    
    enemies = [
        Enemy("Goblin Scout", max_hp=10, attack=2),
        Enemy("Orc Warrior", max_hp=15, attack=4)
    ]
    
    print(f"Player: {player.name} (HP: {player.hp}, Mana: {player.mana})")
    print("Enemies:")
    for enemy in enemies:
        print(f"  - {enemy.name} (HP: {enemy.hp}, Attack: {enemy.attack})")
    
    # Inicializar gameplay engine
    gameplay = GameplayEngine(player, enemies)
    gameplay.start_game()
    
    # Mostrar estado inicial
    state = gameplay.get_game_state()
    print(f"\nGame State: {state['game_state']}")
    print(f"Turn: {state['turn_count']}")
    print(f"Player: {state['player']['hp']}/{state['player']['max_hp']} HP, {state['player']['mana']}/{state['player']['max_mana']} Mana")
    
    # Mostrar cartas na mão
    playable = gameplay.get_playable_cards()
    print(f"\nPlayable cards ({len(playable)}):")
    for i, card in enumerate(playable):
        print(f"  {i+1}. {card}")
    
    # Simular algumas jogadas
    if playable:
        print(f"\n--- Simulating plays ---")
        
        # Jogar primeira carta
        card = playable[0]
        targets = None
        
        # Se for magia de dano, mirar nos inimigos
        if hasattr(card, 'spell_type') and card.spell_type in [SpellType.DAMAGE, SpellType.AOE]:
            targets = gameplay.get_alive_enemies()
        
        print(f"Playing: {card.name}")
        success = gameplay.player_turn_action("play_card", card=card, targets=targets)
        print(f"Result: {'✅ Success' if success else '❌ Failed'}")
        
        # Mostrar estado após jogada
        state = gameplay.get_game_state()
        print(f"Player Mana: {state['player']['mana']}/{state['player']['max_mana']}")
        print(f"Cards played this turn: {state['cards_played_this_turn']}/{state['max_cards_per_turn']}")
    
    # Terminar turno do jogador
    print(f"\n--- Ending player turn ---")
    gameplay.end_player_turn()
    
    # Mostrar estado final
    final_state = gameplay.get_game_state()
    print(f"Final Game State: {final_state['game_state']}")
    
    return gameplay


def main():
    """Executa todas as demonstrações."""
    print("🏰 MEDIEVAL DECK - GAMEPLAY SYSTEM DEMO 🏰")
    print("=" * 50)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s - %(levelname)s: %(message)s'
    )
    
    try:
        # Demo 1: Criação de cartas
        cards = demo_card_creation()
        
        # Demo 2: Sistema de deck
        deck, player = demo_deck_system()
        
        # Demo 3: Gameplay completo
        gameplay = demo_full_gameplay()
        
        print(f"\n" + "=" * 50)
        print("✅ FASE 2 - SISTEMA DE CARTAS IMPLEMENTADO!")
        print("✅ Todos os componentes funcionando:")
        print("   - ✅ TurnEngine (Fase 1)")
        print("   - ✅ Card System")
        print("   - ✅ Deck Management") 
        print("   - ✅ Gameplay Engine")
        print("   - ✅ Integração completa")
        
        # Salvar estado do jogo
        if hasattr(gameplay, 'save_game_state'):
            save_path = "demo_game_state.json"
            if gameplay.save_game_state(save_path):
                print(f"   - ✅ Game state saved to {save_path}")
        
        print(f"\n🎯 Próximo passo: Fase 3 - Enemies/AI conforme roadmap")
        
    except Exception as e:
        print(f"❌ Erro durante demonstração: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎉 Demo concluída com sucesso!")
    else:
        print(f"\n💥 Demo falhou - verificar logs acima")
        sys.exit(1)
