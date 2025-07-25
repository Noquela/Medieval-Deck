"""
Medieval Deck - Sistema de Combate Inteligente

Integra o sistema de inimigos inteligentes com o gameplay principal.
Implementa a Fase 3 do roadmap com IA avançada.
"""

import logging
from typing import List, Dict, Any, Optional
import random

from ..gameplay.gameplay_engine import GameplayEngine
from ..core.turn_engine import Player, GameState
from .smart_enemies import (
    SmartEnemy, EnemyFactory, DifficultyManager,
    EnemyType, AIBehavior, DifficultyLevel
)
from .ai_system import AIBehaviorSystem

logger = logging.getLogger(__name__)


class IntelligentCombatEngine(GameplayEngine):
    """
    Engine de combate com IA avançada.
    
    Extende o GameplayEngine com inimigos inteligentes e IA adaptativa.
    """
    
    def __init__(self, player: Player, enemies: List = None, encounter_type: str = "goblin_patrol"):
        """
        Inicializa o engine de combate inteligente.
        
        Args:
            player: Jogador
            enemies: Lista de inimigos (opcional)
            encounter_type: Tipo de encontro
        """
        # Se enemies não fornecidos, criar inimigos inteligentes
        if enemies is None:
            self.difficulty_manager = DifficultyManager()
            current_difficulty = self.difficulty_manager.current_difficulty
            smart_enemies = EnemyFactory.create_encounter(encounter_type, current_difficulty)
        else:
            smart_enemies = enemies
            self.difficulty_manager = DifficultyManager()
        
        # Inicializar com inimigos inteligentes
        super().__init__(player, smart_enemies)
        
        # Sistema de IA
        self.ai_system = AIBehaviorSystem()
        self.encounter_type = encounter_type
        self.combat_log = []
        
        # Conectar IA ao player para análise
        self.player.ai_system = self.ai_system
        
        logger.info(f"Intelligent Combat Engine initialized with {encounter_type}")
        logger.info(f"Enemies: {[str(e) for e in smart_enemies]}")
    
    def start_game(self) -> None:
        """Inicia o combate inteligente."""
        logger.info("=== INTELLIGENT MEDIEVAL DECK COMBAT START ===")
        logger.info(f"Encounter: {self.encounter_type}")
        logger.info(f"Difficulty: {self.difficulty_manager.current_difficulty.value}")
        
        # Inicializar gameplay normal
        super().start_game()
        
        # Adicionar informações de IA
        for enemy in self.enemies:
            if isinstance(enemy, SmartEnemy):
                logger.info(f"  - {enemy} (AI: {enemy.ai_behavior.value})")
    
    def set_enemies(self, enemies: List) -> None:
        """
        Configura novos inimigos para o combate.
        
        Args:
            enemies: Lista de inimigos
        """
        self.enemies = enemies
        logger.info(f"Combat engine configured with {len(enemies)} enemies")
        for enemy in enemies:
            if isinstance(enemy, SmartEnemy):
                logger.info(f"  - {enemy} (AI: {enemy.ai_behavior.value})")
    
    def play_card(self, card, targets: List[Any] = None) -> bool:
        """
        Joga uma carta e registra para análise da IA.
        """
        # Registrar ação para IA
        action_data = {
            "type": "play_card",
            "card_name": card.name,
            "card_type": card.card_type.value,
            "cost": card.cost,
            "targets": len(targets) if targets else 0,
            "target_type": "enemy" if targets else "none",
            "mana_spent": card.cost,
            "turn": self.turn_count
        }
        
        self.ai_system.process_player_action(action_data)
        
        # Executar jogada normal
        result = super().play_card(card, targets)
        
        if result:
            # Log para combate
            self.combat_log.append({
                "turn": self.turn_count,
                "actor": "player",
                "action": "play_card",
                "card": card.name,
                "success": True
            })
        
        return result
    
    def _execute_enemy_turns(self) -> None:
        """Executa turnos dos inimigos com IA avançada."""
        logger.info("\n--- Intelligent Enemy Turns ---")
        
        alive_enemies = self.get_alive_enemies()
        player_creatures = self.get_alive_player_creatures()
        
        for enemy in alive_enemies:
            if not enemy.is_alive:
                continue
            
            logger.info(f"\n{enemy.name}'s turn:")
            
            # Executar início do turno
            if isinstance(enemy, SmartEnemy):
                enemy.on_turn_start()
            
            # IA avançada para inimigos inteligentes
            if isinstance(enemy, SmartEnemy):
                self._execute_smart_enemy_turn(enemy, player_creatures)
            else:
                # IA básica para inimigos normais
                self._enemy_ai_turn(enemy)
        
        logger.info("--- End Intelligent Enemy Turns ---\n")
    
    def _execute_smart_enemy_turn(self, enemy: SmartEnemy, player_creatures: List) -> None:
        """
        Executa turno de inimigo inteligente.
        
        Args:
            enemy: Inimigo inteligente
            player_creatures: Criaturas do jogador
        """
        # Obter decisão da IA avançada
        ai_decision = self.ai_system.get_ai_decision(
            enemy=enemy,
            player=self.player,
            player_creatures=player_creatures,
            game_context={
                "turn": self.turn_count,
                "encounter_type": self.encounter_type
            }
        )
        
        # Inimigo decide ação baseado em sua IA específica
        enemy_action = enemy.decide_action(self.player, player_creatures)
        
        # Combinar decisões para ação final
        final_action = self._combine_ai_decisions(enemy_action, ai_decision, enemy)
        
        # Executar ação
        success = enemy.execute_action(final_action)
        
        # Registrar para aprendizado
        combat_result = {
            "strategy_used": ai_decision.get("primary_strategy"),
            "action_taken": final_action.get("type"),
            "player_took_damage": final_action.get("damage", 0) if success else 0,
            "success": success
        }
        
        self.ai_system.adapt_to_player(combat_result)
        
        # Log para combate
        self.combat_log.append({
            "turn": self.turn_count,
            "actor": enemy.name,
            "action": final_action.get("type", "unknown"),
            "ai_strategy": ai_decision.get("primary_strategy"),
            "success": success
        })
    
    def _combine_ai_decisions(
        self,
        enemy_action: Dict[str, Any],
        ai_decision: Dict[str, Any],
        enemy: SmartEnemy
    ) -> Dict[str, Any]:
        """
        Combina decisão do inimigo específico com IA global.
        
        Args:
            enemy_action: Ação decidida pelo inimigo
            ai_decision: Decisão da IA global
            enemy: Inimigo que está agindo
            
        Returns:
            Ação final combinada
        """
        strategy = ai_decision.get("primary_strategy", "aggressive")
        
        # Modificar ação baseada na estratégia global
        if strategy == "survival" and enemy.hp <= enemy.max_hp * 0.3:
            # Priorizar sobrevivência
            if "life_drain" in enemy.special_abilities and enemy._can_use_ability("life_drain"):
                return enemy._use_special_ability("life_drain", self.player)
        
        elif strategy == "pressure" and enemy_action.get("type") == "attack":
            # Aumentar pressão - focar no jogador
            if enemy_action.get("target") != self.player:
                enemy_action["target"] = self.player
                enemy_action["damage"] = int(enemy_action.get("damage", 0) * 1.2)
        
        elif strategy == "board_control":
            # Focar em criaturas do jogador
            player_creatures = self.get_alive_player_creatures()
            if player_creatures and enemy_action.get("type") == "attack":
                # Atacar criatura mais forte
                strongest = max(player_creatures, key=lambda c: c.attack)
                enemy_action["target"] = strongest
        
        return enemy_action
    
    def end_player_turn(self) -> bool:
        """Termina turno do jogador com análise de IA."""
        # Registrar fim de turno
        turn_action = {
            "type": "end_turn",
            "turn": self.turn_count,
            "cards_played": self.cards_played_this_turn,
            "mana_remaining": self.player.mana
        }
        
        self.ai_system.process_player_action(turn_action)
        
        # Executar fim de turno normal
        return super().end_player_turn()
    
    def _check_combat_end(self) -> Optional[str]:
        """Verifica se o combate terminou e atualiza dificuldade."""
        game_state = self.turn_engine.check_end()
        
        if game_state == GameState.VICTORY:
            # Jogador venceu
            self.difficulty_manager.adjust_difficulty(True)
            logger.info("🎉 COMBAT VICTORY! Difficulty may increase.")
            return "victory"
            
        elif game_state == GameState.GAME_OVER:
            # Jogador perdeu
            self.difficulty_manager.adjust_difficulty(False)
            logger.info("💀 COMBAT DEFEAT! Difficulty may decrease.")
            return "defeat"
        
        return None
    
    def get_combat_summary(self) -> Dict[str, Any]:
        """Retorna resumo do combate."""
        base_state = self.get_game_state()
        
        # Adicionar informações específicas do combate inteligente
        ai_stats = self.ai_system.get_ai_stats()
        difficulty_stats = self.difficulty_manager.get_stats()
        
        smart_enemies_info = []
        for enemy in self.enemies:
            if isinstance(enemy, SmartEnemy):
                smart_enemies_info.append({
                    "name": enemy.name,
                    "type": enemy.enemy_type.value,
                    "ai_behavior": enemy.ai_behavior.value,
                    "hp": f"{enemy.hp}/{enemy.max_hp}",
                    "special_abilities": enemy.special_abilities,
                    "active_buffs": list(enemy.buffs.keys())
                })
        
        base_state.update({
            "encounter_type": self.encounter_type,
            "difficulty_level": self.difficulty_manager.current_difficulty.value,
            "smart_enemies": smart_enemies_info,
            "ai_analysis": ai_stats,
            "difficulty_stats": difficulty_stats,
            "combat_log": self.combat_log[-10:],  # Últimas 10 ações
            "total_turns": self.turn_count
        })
        
        return base_state
    
    def save_combat_data(self, file_path: str) -> bool:
        """
        Salva dados completos do combate.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se salvou com sucesso
        """
        try:
            import json
            
            combat_data = {
                "summary": self.get_combat_summary(),
                "full_combat_log": self.combat_log,
                "ai_learning_data": self.ai_system.get_ai_stats(),
                "difficulty_progression": self.difficulty_manager.get_stats()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(combat_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Combat data saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save combat data: {e}")
            return False


class EncounterManager:
    """
    Gerencia diferentes tipos de encontros e progressão.
    """
    
    def __init__(self, difficulty_manager=None):
        self.encounters_completed = []
        self.current_level = 1
        self.boss_encounters = ["dragon_lair", "wizard_tower"]
        self.difficulty_manager = difficulty_manager
        
    def get_next_encounter(self, difficulty: DifficultyLevel) -> str:
        """
        Determina o próximo encontro baseado na progressão.
        
        Args:
            difficulty: Nível de dificuldade atual
            
        Returns:
            Tipo do próximo encontro
        """
        # Encontros básicos por nível
        level_encounters = {
            1: ["goblin_patrol", "goblin_patrol"],
            2: ["goblin_patrol", "orc_warband"],
            3: ["orc_warband", "undead_horde"],
            4: ["undead_horde", "mixed_encounter"],
            5: ["wizard_tower"],  # Boss
            6: ["dragon_lair"]   # Final boss
        }
        
        available = level_encounters.get(self.current_level, ["mixed_encounter"])
        
        # Adicionar variedade baseada na dificuldade
        if difficulty == DifficultyLevel.HARD or difficulty == DifficultyLevel.NIGHTMARE:
            if self.current_level >= 3:
                available.extend(self.boss_encounters)
        
        encounter = random.choice(available)
        logger.info(f"Next encounter selected: {encounter} (Level {self.current_level})")
        
        return encounter
    
    def complete_encounter(self, encounter_type: str, victory: bool) -> None:
        """
        Registra conclusão de encontro.
        
        Args:
            encounter_type: Tipo do encontro
            victory: Se foi vitória do jogador
        """
        self.encounters_completed.append({
            "type": encounter_type,
            "victory": victory,
            "level": self.current_level
        })
        
        # Avançar nível após vitórias
        if victory and len(self.encounters_completed) % 2 == 0:
            self.current_level += 1
            logger.info(f"Player advanced to level {self.current_level}!")
    
    def get_progression_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de progressão."""
        victories = sum(1 for e in self.encounters_completed if e["victory"])
        total = len(self.encounters_completed)
        
        return {
            "current_level": self.current_level,
            "encounters_completed": total,
            "victories": victories,
            "win_rate": victories / total if total > 0 else 0,
            "encounters_by_type": {
                encounter["type"]: sum(1 for e in self.encounters_completed if e["type"] == encounter["type"])
                for encounter in self.encounters_completed
            }
        }
    
    def create_adaptive_encounter(self, encounter_type: str) -> List['SmartEnemy']:
        """
        Cria um encontro adaptativo baseado na dificuldade atual.
        
        Args:
            encounter_type: Tipo base do encontro
            
        Returns:
            Lista de inimigos para o encontro
        """
        from .smart_enemies import EnemyFactory, DifficultyLevel
        
        # Determinar dificuldade
        if self.difficulty_manager:
            difficulty = self.difficulty_manager.current_difficulty
        else:
            difficulty = DifficultyLevel.MEDIUM
        
        # Criar encontro baseado no tipo
        enemies = EnemyFactory.create_encounter(encounter_type, difficulty)
        
        return enemies
    
    def start_encounter(self, enemies: List = None) -> bool:
        """
        Inicia um encontro com inimigos específicos ou cria novos.
        
        Args:
            enemies: Lista de inimigos (opcional, cria automaticamente se None)
            
        Returns:
            True se o encontro foi iniciado com sucesso
        """
        try:
            if enemies:
                # Usar inimigos fornecidos
                self.enemies = enemies
                logger.info(f"Encontro iniciado com {len(enemies)} inimigos fornecidos")
            else:
                # Criar encontro automático
                auto_enemies = self.create_adaptive_encounter("mixed")
                self.enemies = auto_enemies
                logger.info(f"Encontro automático criado com {len(auto_enemies)} inimigos")
            
            # Inicializar estado do combate
            self.start_game()
            
            logger.info("Encontro iniciado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar encontro: {e}")
            return False
