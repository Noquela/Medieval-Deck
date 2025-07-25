"""
Demo da UI de Combate - Medieval Deck

Demonstra a interface completa de combate com cartas, inimigos e interações.
"""

import pygame
import sys
import logging
from pathlib import Path

# Adicionar src ao path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.ui.combat_screen import CombatScreen
from src.enemies.intelligent_combat import IntelligentCombatEngine
from src.gameplay.cards import CardType
from src.gameplay.deck import Deck, DeckBuilder
from src.core.turn_engine import Player

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_demo_player() -> Player:
    """Cria um jogador para o demo."""
    # Criar player com parâmetros corretos
    player = Player(max_hp=30, max_mana=10)
    
    # Criar deck de exemplo usando DeckBuilder
    deck = DeckBuilder.create_starter_deck("balanced")
    
    # Atribuir deck ao player
    player.deck = deck
    
    return player


def main():
    """Função principal do demo."""
    print("=== DEMO - UI DE COMBATE ===")
    print("Medieval Deck - Fase 4 (Interface e UX)")
    print()
    
    try:
        # Inicializar Pygame
        pygame.init()
        
        # Configurar tela
        width, height = 1280, 720
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Medieval Deck - Combat UI Demo")
        
        # Criar player
        player = create_demo_player()
        
        # Criar combat engine
        combat_engine = IntelligentCombatEngine(player, encounter_type="goblin_patrol")
        
        # NÃO chamar start_game() - queremos o combate manual via UI
        # combat_engine.start_game()
        
        print("✅ Combat engine inicializado")
        print(f"Player: Demo Player - HP: {player.hp}/{player.max_hp}")
        print(f"Enemies: {len(combat_engine.get_alive_enemies())}")
        print(f"Hand size: {len(combat_engine.get_playable_cards())}")
        print()
        
        # Criar tela de combate
        combat_screen = CombatScreen(screen, combat_engine)
        
        print("🎮 Iniciando interface de combate...")
        print()
        print("CONTROLES:")
        print("  • Mouse: Selecionar cartas e alvos")
        print("  • Clique esquerdo: Selecionar/Usar")
        print("  • Clique direito: Cancelar")
        print("  • ESC: Pausar/Cancelar")
        print("  • SPACE: Finalizar turno")
        print("  • Fechar janela: Sair")
        print()
        
        # Executar tela de combate
        result = combat_screen.run()
        
        # Resultado final
        if result:
            print("🎉 VITÓRIA! Combate concluído com sucesso!")
        else:
            print("💀 DERROTA! Tente novamente.")
            
        return result
        
    except Exception as e:
        logger.error(f"Erro durante o demo: {e}", exc_info=True)
        return False
        
    finally:
        pygame.quit()
        print("\n=== DEMO FINALIZADO ===")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
