"""
Testes para o TurnEngine - Fase 1 do roadmap.
"""

import sys
import unittest
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import diretamente para evitar dependências do pygame
from core.turn_engine import TurnEngine, Player, Enemy, GameState, TurnPhase


class TestPlayer(unittest.TestCase):
    """Testes para a classe Player."""
    
    def setUp(self):
        self.player = Player(max_hp=30, max_mana=10)
    
    def test_player_initialization(self):
        """Testa inicialização do jogador."""
        self.assertEqual(self.player.hp, 30)
        self.assertEqual(self.player.max_hp, 30)
        self.assertEqual(self.player.mana, 10)
        self.assertEqual(self.player.max_mana, 10)
        self.assertTrue(self.player.is_alive)
    
    def test_take_damage(self):
        """Testa sistema de dano."""
        damage_dealt = self.player.take_damage(10)
        self.assertEqual(damage_dealt, 10)
        self.assertEqual(self.player.hp, 20)
        self.assertTrue(self.player.is_alive)
    
    def test_player_death(self):
        """Testa morte do jogador."""
        self.player.take_damage(35)  # Mais que o HP máximo
        self.assertEqual(self.player.hp, 0)
        self.assertFalse(self.player.is_alive)
    
    def test_healing(self):
        """Testa sistema de cura."""
        self.player.take_damage(15)  # HP = 15
        healed = self.player.heal(10)
        self.assertEqual(healed, 10)
        self.assertEqual(self.player.hp, 25)
    
    def test_overheal_prevention(self):
        """Testa que não pode curar além do máximo."""
        healed = self.player.heal(50)
        self.assertEqual(healed, 0)  # Já está no máximo
        self.assertEqual(self.player.hp, 30)
    
    def test_mana_spending(self):
        """Testa gasto de mana."""
        result = self.player.spend_mana(5)
        self.assertTrue(result)
        self.assertEqual(self.player.mana, 5)
    
    def test_insufficient_mana(self):
        """Testa gasto de mana insuficiente."""
        result = self.player.spend_mana(15)  # Mais que o máximo
        self.assertFalse(result)
        self.assertEqual(self.player.mana, 10)  # Não mudou


class TestEnemy(unittest.TestCase):
    """Testes para a classe Enemy."""
    
    def setUp(self):
        self.enemy = Enemy("Test Goblin", max_hp=10, attack=3, defense=1)
    
    def test_enemy_initialization(self):
        """Testa inicialização do inimigo."""
        self.assertEqual(self.enemy.name, "Test Goblin")
        self.assertEqual(self.enemy.hp, 10)
        self.assertEqual(self.enemy.attack, 3)
        self.assertEqual(self.enemy.defense, 1)
        self.assertTrue(self.enemy.is_alive)
    
    def test_take_damage_with_defense(self):
        """Testa dano com defesa."""
        damage_dealt = self.enemy.take_damage(5)  # 5 - 1 defense = 4
        self.assertEqual(damage_dealt, 4)
        self.assertEqual(self.enemy.hp, 6)
    
    def test_minimum_damage(self):
        """Testa que sempre aplica pelo menos 1 de dano."""
        damage_dealt = self.enemy.take_damage(1)  # 1 - 1 defense = 1 (mínimo)
        self.assertEqual(damage_dealt, 1)
        self.assertEqual(self.enemy.hp, 9)
    
    def test_enemy_death(self):
        """Testa morte do inimigo."""
        self.enemy.take_damage(20)  # Mais que o HP
        self.assertEqual(self.enemy.hp, 0)
        self.assertFalse(self.enemy.is_alive)
    
    def test_get_action(self):
        """Testa ação básica do inimigo."""
        action = self.enemy.get_action()
        self.assertEqual(action["type"], "attack")
        self.assertEqual(action["damage"], 3)


class TestTurnEngine(unittest.TestCase):
    """Testes para a classe TurnEngine."""
    
    def setUp(self):
        self.player = Player(max_hp=30, max_mana=10)
        self.enemies = [
            Enemy("Goblin", max_hp=8, attack=2, defense=0),
            Enemy("Orc", max_hp=15, attack=4, defense=1)
        ]
        self.engine = TurnEngine(self.player, self.enemies)
    
    def test_engine_initialization(self):
        """Testa inicialização do engine."""
        self.assertEqual(self.engine.player, self.player)
        self.assertEqual(len(self.engine.enemies), 2)
        self.assertEqual(self.engine.game_state, GameState.MENU)
        self.assertEqual(self.engine.turn_count, 0)
        self.assertFalse(self.engine.is_running)
    
    def test_check_end_conditions(self):
        """Testa condições de fim de jogo."""
        # Jogo não deve terminar no início
        self.assertIsNone(self.engine.check_end())
        
        # Teste de derrota
        self.player.take_damage(50)
        self.assertEqual(self.engine.check_end(), 'defeat')
        
        # Reset para teste de vitória
        self.player.hp = 30
        self.player.is_alive = True
        
        # Teste de vitória
        for enemy in self.enemies:
            enemy.take_damage(50)
        self.assertEqual(self.engine.check_end(), 'victory')
    
    def test_get_alive_enemies(self):
        """Testa filtro de inimigos vivos."""
        alive = self.engine.get_alive_enemies()
        self.assertEqual(len(alive), 2)
        
        # Matar um inimigo
        self.enemies[0].take_damage(50)
        alive = self.engine.get_alive_enemies()
        self.assertEqual(len(alive), 1)
        self.assertEqual(alive[0].name, "Orc")
    
    def test_game_info(self):
        """Testa informações do jogo."""
        self.engine.turn_count = 5
        self.engine.game_state = GameState.PLAYER_TURN
        
        info = self.engine.get_game_info()
        self.assertEqual(info["turn_count"], 5)
        self.assertEqual(info["game_state"], "player_turn")
        self.assertEqual(info["player_hp"], "30/30")
        self.assertEqual(info["alive_enemies"], 2)
    
    def test_stop_engine(self):
        """Testa parada do engine."""
        self.engine.is_running = True
        self.engine.stop()
        self.assertFalse(self.engine.is_running)
        self.assertEqual(self.engine.game_state, GameState.MENU)


if __name__ == '__main__':
    # Configurar logging para os testes
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Executar testes
    unittest.main(verbosity=2)
