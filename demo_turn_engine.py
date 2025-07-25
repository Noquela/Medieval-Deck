"""
Demonstração do TurnEngine - Fase 1 implementada.

Script de exemplo para testar o sistema de turnos básico.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import diretamente para evitar dependências do pygame
from core.turn_engine import TurnEngine, Player, Enemy
from utils.helpers import setup_logging


def demo_turn_engine():
    """Demonstração do sistema de turnos."""
    print("🏰 Medieval Deck - Turn Engine Demo")
    print("=" * 50)
    
    # Setup logging
    setup_logging(level="INFO")
    
    # Criar jogador
    player = Player(max_hp=30, max_mana=10)
    print(f"🛡️ Player created: {player.hp} HP, {player.mana} Mana")
    
    # Criar inimigos conforme roadmap
    enemies = [
        Enemy("Grunt", max_hp=10, attack=2, defense=0),  # Grunt: hp=10, atk=2
        Enemy("Elite Warrior", max_hp=20, attack=5, defense=1)  # Elite: hp=20, atk=5
    ]
    
    print(f"⚔️ Enemies created:")
    for enemy in enemies:
        print(f"   {enemy.name}: {enemy.hp} HP, {enemy.attack} ATK, {enemy.defense} DEF")
    
    # Criar engine
    engine = TurnEngine(player, enemies)
    
    # Configurar callbacks para demonstração
    def on_player_turn_start():
        print(f"\n--- Turn {engine.turn_count} ---")
        info = engine.get_game_info()
        print(f"Player: {info['player_hp']} HP, {info['player_mana']} Mana")
        print(f"Enemies alive: {info['alive_enemies']}")
        time.sleep(1)
    
    def on_victory():
        print("\n🎉 VICTORY! All enemies have been defeated!")
        print("The realm is safe once more!")
    
    def on_game_over():
        print("\n💀 DEFEAT! The darkness has won...")
        print("Better luck next time, brave warrior!")
    
    engine.on_player_turn_start = on_player_turn_start
    engine.on_victory = on_victory
    engine.on_game_over = on_game_over
    
    print(f"\n🎮 Starting combat simulation...")
    print("Press Ctrl+C to stop early")
    
    try:
        # Simulação automática com limitador para evitar loop infinito
        max_turns = 20
        original_main_phase = engine._player_turn_main_phase
        
        def simulated_main_phase():
            """Fase principal simulada com ações automáticas."""
            alive_enemies = engine.get_alive_enemies()
            if alive_enemies:
                target = alive_enemies[0]
                damage = 6  # Dano do jogador
                target.take_damage(damage)
                print(f"   Player attacks {target.name} for {damage} damage!")
                
                if not target.is_alive:
                    print(f"   {target.name} has been defeated!")
            
            time.sleep(0.5)
        
        # Substituir temporariamente para demo
        engine._player_turn_main_phase = simulated_main_phase
        
        # Iniciar engine com limitador
        engine.is_running = True
        engine.game_state = engine.GameState.PLAYER_TURN
        engine.turn_count = 1
        
        while engine.is_running and not engine.check_end() and engine.turn_count <= max_turns:
            if engine.game_state == engine.GameState.PLAYER_TURN:
                engine.player_turn()
            elif engine.game_state == engine.GameState.ENEMY_TURN:
                engine.enemy_turns()
        
        # Verificar resultado final
        final_state = engine.check_end()
        if final_state:
            engine._handle_game_end(final_state)
        elif engine.turn_count > max_turns:
            print(f"\n⏰ Demo ended after {max_turns} turns")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo stopped by user")
        engine.stop()
    
    print(f"\n📊 Final Statistics:")
    info = engine.get_game_info()
    print(f"   Turns played: {info['turn_count']}")
    print(f"   Player HP: {info['player_hp']}")
    print(f"   Enemies remaining: {info['alive_enemies']}")
    print("\n✅ Turn Engine demo completed!")


def test_turn_engine():
    """Executa testes do TurnEngine."""
    print("\n🧪 Running TurnEngine tests...")
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_turn_engine.py", 
            "-v"
        ], cwd=Path(__file__).parent, capture_output=True, text=True)
        
        print("Test Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
    except FileNotFoundError:
        print("⚠️ pytest not found, running basic test...")
        # Fallback: importar e executar teste básico
        from tests.test_turn_engine import TestTurnEngine
        import unittest
        
        suite = unittest.TestLoader().loadTestsFromTestCase(TestTurnEngine)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print("✅ Basic tests passed!")
        else:
            print("❌ Some basic tests failed!")


if __name__ == "__main__":
    print("🏰 Medieval Deck - Fase 1: Turn Engine")
    print("Implementação conforme roadmap detalhado")
    print()
    
    choice = input("Choose option:\n1. Demo\n2. Tests\n3. Both\nChoice (1-3): ").strip()
    
    if choice in ["1", "3"]:
        demo_turn_engine()
    
    if choice in ["2", "3"]:
        test_turn_engine()
    
    print("\n🎯 Fase 1 completa! Próximo: Fase 2 - Mecânicas de Cartas")
