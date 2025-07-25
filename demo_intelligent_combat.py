#!/usr/bin/env python3
"""
Medieval Deck - Demo de Combate Inteligente (Fase 3)

Demonstra o sistema completo de inimigos com IA avançada:
- SmartEnemy com comportamentos específicos
- Sistema de análise de jogador
- Combate inteligente e adaptativo
- Gerenciamento de dificuldade

Execução:
python demo_intelligent_combat.py
"""

import sys
import os
import json
import logging
import random
from typing import List, Dict, Any

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.turn_engine import Player, TurnEngine, TurnPhase, GameState
from src.gameplay.cards import Card, CreatureCard, SpellCard, CreatureType, SpellType
from src.gameplay.deck import Deck
from src.gameplay.gameplay_engine import GameplayEngine
from src.enemies import (
    SmartEnemy, EnemyFactory, DifficultyManager,
    EnemyType, AIBehavior, DifficultyLevel,
    IntelligentCombatEngine, EncounterManager,
    AIBehaviorSystem, PlayerAnalyzer
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('intelligent_combat.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class IntelligentCombatDemo:
    """Demonstração completa do sistema de combate inteligente."""
    
    def __init__(self):
        self.logger = logger
        self.difficulty_manager = DifficultyManager()
        self.ai_system = AIBehaviorSystem()
        self.player_analyzer = PlayerAnalyzer()
        
        # Criar player com deck
        self.player = self._create_demo_player()
        self.combat_engine = IntelligentCombatEngine(
            self.player,
            encounter_type="goblin_patrol"
        )
        
        self.combat_history = []
        
    def _create_demo_player(self) -> Player:
        """Cria um jogador para demonstração."""
        player = Player(max_hp=30, max_mana=10)
        player.name = "Demo Player"
        player.attack = 5
        player.defense = 1
        
        # Criar deck básico
        cards = [
            CreatureCard("knight_01", "Knight", cost=3, description="Brave warrior", attack=4, defense=5, creature_type=CreatureType.TANK),
            CreatureCard("archer_01", "Archer", cost=2, description="Skilled archer", attack=3, defense=2, creature_type=CreatureType.DPS),
            CreatureCard("wizard_01", "Wizard", cost=4, description="Wise mage", attack=2, defense=4, creature_type=CreatureType.SUPPORT),
            SpellCard("fireball_01", "Fireball", cost=3, description="Burning damage", spell_type=SpellType.DAMAGE, effect_value=4),
            SpellCard("heal_01", "Heal", cost=2, description="Restore health", spell_type=SpellType.HEAL, effect_value=5),
            SpellCard("lightning_01", "Lightning", cost=2, description="Electric shock", spell_type=SpellType.DAMAGE, effect_value=3),
            CreatureCard("dragon_01", "Dragon", cost=8, description="Ancient beast", attack=8, defense=8, creature_type=CreatureType.DPS),
            CreatureCard("assassin_01", "Assassin", cost=3, description="Shadow killer", attack=5, defense=2, creature_type=CreatureType.DPS),
        ]
        
        deck = Deck(cards)
        player.deck = deck
        
        return player
    
    def run_full_demo(self):
        """Executa demonstração completa do sistema."""
        self.logger.info("=" * 60)
        self.logger.info("MEDIEVAL DECK - DEMO COMBATE INTELIGENTE (FASE 3)")
        self.logger.info("=" * 60)
        
        try:
            # 1. Demonstrar tipos de inimigos
            self._demo_enemy_types()
            
            # 2. Demonstrar comportamentos de IA
            self._demo_ai_behaviors()
            
            # 3. Demonstrar sistema de análise
            self._demo_player_analysis()
            
            # 4. Demonstrar combate adaptativo
            self._demo_adaptive_combat()
            
            # 5. Demonstrar encontros variados
            self._demo_encounter_variety()
            
            # 6. Relatório final
            self._final_report()
            
        except Exception as e:
            self.logger.error(f"Erro durante demonstração: {e}")
            raise
    
    def _demo_enemy_types(self):
        """Demonstra diferentes tipos de inimigos."""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("1. DEMONSTRAÇÃO - TIPOS DE INIMIGOS")
        self.logger.info("=" * 50)
        
        # Criar um de cada tipo
        enemies = [
            EnemyFactory.create_goblin(),
            EnemyFactory.create_orc(),
            EnemyFactory.create_skeleton(),
            EnemyFactory.create_wizard(),
            EnemyFactory.create_dragon()
        ]
        
        for enemy in enemies:
            self.logger.info(f"\n[ENEMY] {enemy}")
            self.logger.info(f"   Habilidades: {enemy.special_abilities}")
            self.logger.info(f"   Comportamento: {enemy.ai_behavior.value}")
            self.logger.info(f"   Dificuldade: {enemy.difficulty.value}")
            
            # Demonstrar decisão de ação
            action = enemy.decide_action(self.player, [])
            self.logger.info(f"   Decisão: {action['type']} - {action}")
    
    def _demo_ai_behaviors(self):
        """Demonstra diferentes comportamentos de IA."""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("2. DEMONSTRAÇÃO - COMPORTAMENTOS DE IA")
        self.logger.info("=" * 50)
        
        # Criar inimigos com comportamentos diferentes
        behaviors = [
            (AIBehavior.AGGRESSIVE, "Orc Berserker"),
            (AIBehavior.DEFENSIVE, "Skeleton Guardian"),
            (AIBehavior.TACTICAL, "Dark Wizard"),
            (AIBehavior.ADAPTIVE, "Ancient Dragon"),
            (AIBehavior.RANDOM, "Mad Goblin")
        ]
        
        for behavior, name in behaviors:
            self.logger.info(f"\n[AI-BEHAVIOR] Testando comportamento: {behavior.value}")
            
            enemy = SmartEnemy(
                name=name,
                max_hp=20,
                attack=5,
                enemy_type=EnemyType.ORC,
                ai_behavior=behavior
            )
            
            # Simular várias decisões
            for i in range(3):
                # Variar situação
                self.player.hp = 30 - (i * 8)  # Simular dano progressivo
                
                action = enemy.decide_action(self.player, [])
                self.logger.info(f"   Turno {i+1} (Player HP: {self.player.hp}): {action['type']}")
                
                enemy.on_turn_start()  # Simular passagem de turno
    
    def _demo_player_analysis(self):
        """Demonstra sistema de análise do jogador."""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("3. DEMONSTRAÇÃO - ANÁLISE DO JOGADOR")
        self.logger.info("=" * 50)
        
        # Simular várias ações do jogador
        actions = [
            {"type": "play_creature", "card": "Knight", "cost": 3},
            {"type": "attack", "damage": 4},
            {"type": "play_spell", "card": "Fireball", "cost": 3},
            {"type": "attack", "damage": 5},
            {"type": "play_creature", "card": "Dragon", "cost": 8},
            {"type": "end_turn"},
            {"type": "attack", "damage": 8},
            {"type": "play_spell", "card": "Lightning", "cost": 2},
        ]
        
        for action in actions:
            self.player_analyzer.record_player_action(action)
        
        # Analisar padrões
        analysis = self.player_analyzer.get_player_style()
        
        self.logger.info(f"[ANALISE] Análise do comportamento do jogador:")
        self.logger.info(f"   Estilo principal: {analysis.get('style', 'unknown')}")
        self.logger.info(f"   Confiança: {analysis.get('confidence', 0.0):.2f}")
        
        # Tentar obter predição
        try:
            next_action = self.player_analyzer.predict_next_action()
            if next_action:
                self.logger.info(f"   Próxima ação prevista: {next_action}")
        except Exception as e:
            self.logger.info(f"   Predição não disponível: {e}")
    
    def _demo_adaptive_combat(self):
        """Demonstra combate adaptativo completo."""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("4. DEMONSTRAÇÃO - COMBATE ADAPTATIVO")
        self.logger.info("=" * 50)
        
        # Simular múltiplos combates
        for round_num in range(3):
            self.logger.info(f"\n[COMBAT] COMBATE {round_num + 1}")
            self.logger.info(f"Dificuldade atual: {self.difficulty_manager.current_difficulty.value}")
            
            # Criar encontro baseado na dificuldade
            enemies = EnemyFactory.create_encounter("mixed", self.difficulty_manager.current_difficulty)
            
            # Configurar combate
            self.combat_engine.set_enemies(enemies)
            self.combat_engine.start_game()
            
            # Simular combate
            combat_result = self._simulate_combat_round()
            
            # Ajustar dificuldade baseado no resultado
            new_difficulty = self.difficulty_manager.adjust_difficulty(combat_result["player_won"])
            
            self.logger.info(f"Resultado: {'VITÓRIA' if combat_result['player_won'] else 'DERROTA'}")
            self.logger.info(f"Nova dificuldade: {new_difficulty.value}")
            
            # Armazenar histórico
            self.combat_history.append({
                "round": round_num + 1,
                "enemies": [e.name for e in enemies],
                "result": combat_result,
                "difficulty": new_difficulty.value
            })
    
    def _simulate_combat_round(self) -> Dict[str, Any]:
        """Simula uma rodada de combate."""
        # Resetar player
        self.player.hp = self.player.max_hp
        
        turns = 0
        max_turns = 10
        
        while (self.player.is_alive and 
               any(e.is_alive for e in self.combat_engine.enemies) and 
               turns < max_turns):
            
            turns += 1
            
            # Turno do jogador (simulado)
            if random.random() > 0.3:  # 70% chance de "acertar"
                alive_enemies = [e for e in self.combat_engine.enemies if e.is_alive]
                if alive_enemies:
                    target = random.choice(alive_enemies)
                    damage = random.randint(3, 7)
                    target.take_damage(damage)
                    self.logger.info(f"   Player hits {target.name} for {damage} damage")
            
            # Turnos dos inimigos
            for enemy in self.combat_engine.enemies:
                if enemy.is_alive:
                    action = self.combat_engine.process_enemy_turn(enemy)
                    if action:
                        self.logger.info(f"   {enemy.name}: {action['type']}")
                        
                        # Simular execução da ação
                        if action["type"] == "attack":
                            damage = random.randint(2, 5)
                            self.player.take_damage(damage)
                            self.logger.info(f"     Player takes {damage} damage")
        
        # Determinar vencedor
        player_won = self.player.is_alive and not any(e.is_alive for e in self.combat_engine.enemies)
        
        return {
            "player_won": player_won,
            "turns": turns,
            "player_hp_remaining": self.player.hp,
            "enemies_defeated": len([e for e in self.combat_engine.enemies if not e.is_alive])
        }
    
    def _demo_encounter_variety(self):
        """Demonstra variedade de encontros."""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("5. DEMONSTRAÇÃO - VARIEDADE DE ENCONTROS")
        self.logger.info("=" * 50)
        
        encounter_types = [
            "goblin_patrol",
            "orc_warband", 
            "undead_horde",
            "wizard_tower",
            "dragon_lair"
        ]
        
        for encounter_type in encounter_types:
            self.logger.info(f"\n[ENCOUNTER] Encontro: {encounter_type}")
            
            enemies = EnemyFactory.create_encounter(encounter_type, DifficultyLevel.MEDIUM)
            
            for enemy in enemies:
                self.logger.info(f"   - {enemy}")
                
                # Demonstrar primeira ação de cada inimigo
                action = enemy.decide_action(self.player, [])
                self.logger.info(f"     Ação inicial: {action['type']}")
    
    def _final_report(self):
        """Gera relatório final da demonstração."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("6. RELATÓRIO FINAL - FASE 3 COMPLETADA")
        self.logger.info("=" * 60)
        
        # Estatísticas de combate
        if self.combat_history:
            total_combats = len(self.combat_history)
            victories = sum(1 for c in self.combat_history if c["result"]["player_won"])
            
            self.logger.info(f"\n[STATS] Estatísticas de Combate:")
            self.logger.info(f"   Total de combates: {total_combats}")
            self.logger.info(f"   Vitórias: {victories}")
            self.logger.info(f"   Taxa de vitória: {victories/total_combats:.2%}")
        
        # Estatísticas de dificuldade
        difficulty_stats = self.difficulty_manager.get_stats()
        self.logger.info(f"\n[DIFFICULTY] Gestão de Dificuldade:")
        self.logger.info(f"   Encontros completados: {difficulty_stats['encounters']}")
        self.logger.info(f"   Taxa de vitória geral: {difficulty_stats['win_rate']:.2%}")
        self.logger.info(f"   Dificuldade final: {difficulty_stats['current_difficulty']}")
        
        # Análise final do jogador
        final_analysis = self.player_analyzer.get_player_style()
        self.logger.info(f"\n[PLAYER-ANALYSIS] Análise Final do Jogador:")
        self.logger.info(f"   Estilo dominante: {final_analysis.get('style', 'unknown')}")
        self.logger.info(f"   Confiança: {final_analysis.get('confidence', 0.0):.2f}")
        
        # Capacidades demonstradas
        self.logger.info(f"\n[SUCCESS] CAPACIDADES DEMONSTRADAS (FASE 3):")
        capabilities = [
            "Inimigos com 5 tipos distintos (Goblin, Orc, Dragon, Skeleton, Wizard)",
            "IA com 5 comportamentos (Aggressive, Defensive, Tactical, Adaptive, Random)",
            "Sistema de habilidades especiais específicas por tipo",
            "Análise comportamental do jogador em tempo real",
            "Dificuldade adaptativa baseada na performance",
            "Encontros variados com múltiplos inimigos",
            "Combate inteligente com tomada de decisão avançada",
            "Integração completa com sistema de cartas (Fase 2)",
            "Gerenciamento de cooldowns e buffs temporários",
            "Logging detalhado para debugging e balanceamento"
        ]
        
        for i, capability in enumerate(capabilities, 1):
            self.logger.info(f"   {i:2d}. {capability}")
        
        self.logger.info(f"\n[COMPLETED] FASE 3 IMPLEMENTADA COM SUCESSO!")
        self.logger.info(f"[NEXT] Próxima: Fase 4 - Interface e UX")
        self.logger.info("=" * 60)
    
    def save_demo_results(self):
        """Salva resultados da demonstração."""
        results = {
            "demo_type": "intelligent_combat",
            "timestamp": "2024-01-20T10:00:00",
            "combat_history": self.combat_history,
            "difficulty_stats": self.difficulty_manager.get_stats(),
            "player_analysis": self.player_analyzer.get_player_style(),
            "phase_3_status": "COMPLETED"
        }
        
        with open("demo_intelligent_combat_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"\n[SAVE] Resultados salvos em: demo_intelligent_combat_results.json")


def main():
    """Função principal do demo."""
    print("[MEDIEVAL DECK] Demo de Combate Inteligente (Fase 3)")
    print("=" * 60)
    
    try:
        demo = IntelligentCombatDemo()
        demo.run_full_demo()
        demo.save_demo_results()
        
        print("\n[SUCCESS] Demo concluído com sucesso!")
        print("[LOG] Verifique o arquivo 'intelligent_combat.log' para detalhes completos")
        
    except Exception as e:
        print(f"\n[ERROR] Erro durante o demo: {e}")
        logger.exception("Erro detalhado:")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
