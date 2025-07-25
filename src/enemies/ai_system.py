"""
Medieval Deck - Sistema de IA Avançada

Implementação da Fase 3 do roadmap:
- Algoritmos de IA para comportamentos específicos
- Sistema de aprendizado e adaptação
- Análise de padrões do jogador
- Estratégias dinâmicas
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import deque, defaultdict
import random
import math

logger = logging.getLogger(__name__)


class PlayerAnalyzer:
    """
    Analisa padrões de comportamento do jogador para IA adaptativa.
    """
    
    def __init__(self, history_size: int = 20):
        self.history_size = history_size
        self.action_history = deque(maxlen=history_size)
        self.card_usage_stats = defaultdict(int)
        self.targeting_patterns = defaultdict(int)
        self.mana_usage_patterns = []
        self.turn_duration_patterns = []
        
    def record_player_action(self, action: Dict[str, Any]) -> None:
        """
        Registra uma ação do jogador para análise.
        
        Args:
            action: Dicionário com dados da ação
        """
        self.action_history.append(action)
        
        # Atualizar estatísticas específicas
        if action.get("type") == "play_card":
            card_name = action.get("card_name", "unknown")
            self.card_usage_stats[card_name] += 1
            
        if action.get("target_type"):
            self.targeting_patterns[action["target_type"]] += 1
            
        if action.get("mana_spent"):
            self.mana_usage_patterns.append(action["mana_spent"])
            if len(self.mana_usage_patterns) > self.history_size:
                self.mana_usage_patterns.pop(0)
                
        if action.get("turn_duration"):
            self.turn_duration_patterns.append(action["turn_duration"])
            if len(self.turn_duration_patterns) > self.history_size:
                self.turn_duration_patterns.pop(0)
    
    def get_player_style(self) -> Dict[str, Any]:
        """
        Analisa o estilo de jogo do jogador.
        
        Returns:
            Dicionário com características do estilo
        """
        if not self.action_history:
            return {"style": "unknown", "confidence": 0.0}
        
        # Analisar agressividade
        aggressive_actions = sum(1 for a in self.action_history 
                               if a.get("target_type") in ["enemy", "enemy_creature"])
        total_actions = len(self.action_history)
        aggression_score = aggressive_actions / total_actions if total_actions > 0 else 0
        
        # Analisar uso de mana (conservador vs gastador)
        if self.mana_usage_patterns:
            avg_mana_per_turn = sum(self.mana_usage_patterns) / len(self.mana_usage_patterns)
            mana_conservation = 1.0 - (avg_mana_per_turn / 10.0)  # Assumindo 10 mana máximo
        else:
            mana_conservation = 0.5
        
        # Analisar velocidade de decisão
        if self.turn_duration_patterns:
            avg_turn_duration = sum(self.turn_duration_patterns) / len(self.turn_duration_patterns)
            decision_speed = 1.0 / (1.0 + avg_turn_duration)  # Inverso da duração
        else:
            decision_speed = 0.5
        
        # Analisar preferências de cartas
        most_used_cards = sorted(self.card_usage_stats.items(), 
                               key=lambda x: x[1], reverse=True)[:3]
        
        # Determinar estilo principal
        style = "balanced"
        confidence = 0.5
        
        if aggression_score > 0.7:
            style = "aggressive"
            confidence = aggression_score
        elif aggression_score < 0.3:
            style = "defensive"
            confidence = 1.0 - aggression_score
        elif mana_conservation > 0.7:
            style = "conservative"
            confidence = mana_conservation
        elif mana_conservation < 0.3:
            style = "reckless"
            confidence = 1.0 - mana_conservation
        
        return {
            "style": style,
            "confidence": confidence,
            "aggression_score": aggression_score,
            "mana_conservation": mana_conservation,
            "decision_speed": decision_speed,
            "preferred_cards": most_used_cards,
            "targeting_preference": dict(self.targeting_patterns)
        }
    
    def predict_next_action(self) -> Optional[str]:
        """
        Prediz o próximo tipo de ação do jogador.
        
        Returns:
            Tipo de ação predita ou None
        """
        if len(self.action_history) < 3:
            return None
        
        # Analisar padrões recentes
        recent_actions = list(self.action_history)[-5:]
        action_types = [a.get("type", "unknown") for a in recent_actions]
        
        # Encontrar padrões comuns
        type_counts = defaultdict(int)
        for action_type in action_types:
            type_counts[action_type] += 1
        
        # Retornar tipo mais comum como predição
        if type_counts:
            return max(type_counts.items(), key=lambda x: x[1])[0]
        
        return None


class StrategyEngine:
    """
    Engine de estratégias para IA avançada.
    """
    
    def __init__(self):
        self.active_strategies = []
        self.strategy_effectiveness = defaultdict(list)
        
    def evaluate_game_state(self, player, enemies, player_creatures) -> Dict[str, float]:
        """
        Avalia o estado atual do jogo.
        
        Returns:
            Métricas do estado do jogo
        """
        # Calcular poder relativo
        player_power = player.hp + sum(c.current_hp + c.attack for c in player_creatures)
        enemy_power = sum(e.hp + e.attack for e in enemies if e.is_alive)
        
        power_ratio = player_power / max(1, enemy_power)
        
        # Calcular pressão temporal
        total_enemy_damage = sum(e.attack for e in enemies if e.is_alive)
        turns_to_death = player.hp / max(1, total_enemy_damage) if total_enemy_damage > 0 else float('inf')
        
        # Calcular controle do campo
        creature_advantage = len(player_creatures) - len([e for e in enemies if e.is_alive])
        
        return {
            "power_ratio": power_ratio,
            "turns_to_death": turns_to_death,
            "creature_advantage": creature_advantage,
            "player_hp_percent": player.hp / player.max_hp,
            "enemy_count": len([e for e in enemies if e.is_alive]),
            "total_enemy_hp": sum(e.hp for e in enemies if e.is_alive)
        }
    
    def recommend_strategy(self, game_state: Dict[str, float], player_style: Dict[str, Any]) -> str:
        """
        Recomenda estratégia baseada no estado do jogo e estilo do jogador.
        
        Args:
            game_state: Métricas do estado atual
            player_style: Estilo de jogo analisado
            
        Returns:
            Nome da estratégia recomendada
        """
        power_ratio = game_state["power_ratio"]
        turns_to_death = game_state["turns_to_death"]
        player_hp_percent = game_state["player_hp_percent"]
        
        # Estratégias baseadas em situação
        if power_ratio > 1.5:
            return "pressure"  # Jogador tem vantagem, manter pressão
        elif power_ratio < 0.5:
            return "survival"  # Inimigo tem vantagem, focar sobrevivência
        elif turns_to_death < 3:
            return "desperation"  # Situação crítica
        elif player_hp_percent > 0.8:
            return "aggressive"  # HP alto, ser agressivo
        elif game_state["creature_advantage"] > 2:
            return "board_control"  # Controle do campo
        else:
            # Adaptar ao estilo do jogador
            player_main_style = player_style.get("style", "balanced")
            if player_main_style == "aggressive":
                return "counter_aggressive"
            elif player_main_style == "defensive":
                return "counter_defensive"
            else:
                return "adaptive"
    
    def get_strategy_actions(self, strategy: str, enemy) -> List[str]:
        """
        Retorna ações recomendadas para uma estratégia.
        
        Args:
            strategy: Nome da estratégia
            enemy: Inimigo que vai executar
            
        Returns:
            Lista de ações recomendadas
        """
        strategy_actions = {
            "aggressive": ["attack_player", "use_damage_ability"],
            "pressure": ["attack_weakest", "use_finishing_move"],
            "survival": ["use_heal", "attack_strongest", "use_defensive_ability"],
            "desperation": ["use_ultimate", "all_out_attack"],
            "counter_aggressive": ["use_defensive_ability", "attack_creatures"],
            "counter_defensive": ["pressure_player", "use_aoe"],
            "board_control": ["clear_creatures", "use_control_ability"],
            "adaptive": ["analyze_and_respond"]
        }
        
        return strategy_actions.get(strategy, ["attack_player"])


class DecisionTree:
    """
    Árvore de decisão para IA complexa.
    """
    
    def __init__(self):
        self.decision_nodes = self._build_decision_tree()
    
    def _build_decision_tree(self) -> Dict[str, Any]:
        """Constrói árvore de decisão para IA."""
        return {
            "root": {
                "condition": "hp_percentage",
                "threshold": 0.3,
                "true_branch": {
                    "condition": "enemy_count",
                    "threshold": 1,
                    "true_branch": {"action": "survival_mode"},
                    "false_branch": {"action": "desperate_attack"}
                },
                "false_branch": {
                    "condition": "player_creatures_count",
                    "threshold": 2,
                    "true_branch": {
                        "condition": "strongest_creature_hp",
                        "threshold": 5,
                        "true_branch": {"action": "focus_fire"},
                        "false_branch": {"action": "area_attack"}
                    },
                    "false_branch": {"action": "attack_player"}
                }
            }
        }
    
    def decide(self, game_state: Dict[str, Any]) -> str:
        """
        Toma decisão usando árvore de decisão.
        
        Args:
            game_state: Estado atual do jogo
            
        Returns:
            Ação decidida
        """
        current_node = self.decision_nodes["root"]
        
        while "condition" in current_node:
            condition = current_node["condition"]
            threshold = current_node["threshold"]
            
            # Avaliar condição
            value = self._evaluate_condition(condition, game_state)
            
            # Navegar na árvore
            if value > threshold:
                current_node = current_node["true_branch"]
            else:
                current_node = current_node["false_branch"]
        
        return current_node.get("action", "attack_player")
    
    def _evaluate_condition(self, condition: str, game_state: Dict[str, Any]) -> float:
        """Avalia uma condição específica."""
        evaluators = {
            "hp_percentage": lambda: game_state.get("enemy_hp_percent", 0.5),
            "enemy_count": lambda: game_state.get("enemy_count", 1),
            "player_creatures_count": lambda: game_state.get("player_creatures_count", 0),
            "strongest_creature_hp": lambda: game_state.get("strongest_creature_hp", 0)
        }
        
        evaluator = evaluators.get(condition, lambda: 0.5)
        return evaluator()


class AIBehaviorSystem:
    """
    Sistema completo de comportamento de IA.
    """
    
    def __init__(self):
        self.player_analyzer = PlayerAnalyzer()
        self.strategy_engine = StrategyEngine()
        self.decision_tree = DecisionTree()
        self.learning_enabled = True
        
    def process_player_action(self, action: Dict[str, Any]) -> None:
        """Processa ação do jogador para aprendizado."""
        if self.learning_enabled:
            self.player_analyzer.record_player_action(action)
    
    def get_ai_decision(
        self,
        enemy,
        player,
        player_creatures: List = None,
        game_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Toma decisão de IA completa considerando todos os fatores.
        
        Args:
            enemy: Inimigo que vai agir
            player: Jogador
            player_creatures: Criaturas do jogador
            game_context: Contexto adicional do jogo
            
        Returns:
            Decisão de IA detalhada
        """
        if player_creatures is None:
            player_creatures = []
        
        # Analisar estilo do jogador
        player_style = self.player_analyzer.get_player_style()
        
        # Avaliar estado do jogo
        enemies = [enemy]  # Simplificado para este exemplo
        game_state = self.strategy_engine.evaluate_game_state(player, enemies, player_creatures)
        
        # Recomendar estratégia
        recommended_strategy = self.strategy_engine.recommend_strategy(game_state, player_style)
        
        # Usar árvore de decisão como backup
        tree_decision = self.decision_tree.decide({
            "enemy_hp_percent": enemy.hp / enemy.max_hp,
            "enemy_count": 1,
            "player_creatures_count": len(player_creatures),
            "strongest_creature_hp": max([c.current_hp for c in player_creatures], default=0)
        })
        
        # Combinar informações para decisão final
        ai_decision = {
            "primary_strategy": recommended_strategy,
            "backup_action": tree_decision,
            "player_style": player_style["style"],
            "confidence": player_style["confidence"],
            "game_state": game_state,
            "reasoning": f"Strategy: {recommended_strategy}, Player: {player_style['style']}"
        }
        
        logger.debug(f"AI Decision for {enemy.name}: {ai_decision['reasoning']}")
        
        return ai_decision
    
    def adapt_to_player(self, combat_result: Dict[str, Any]) -> None:
        """
        Adapta comportamento baseado no resultado do combate.
        
        Args:
            combat_result: Resultado do combate para aprendizado
        """
        if not self.learning_enabled:
            return
        
        # Registrar efetividade das estratégias
        strategy_used = combat_result.get("strategy_used")
        was_effective = combat_result.get("player_took_damage", 0) > 0
        
        if strategy_used:
            self.strategy_engine.strategy_effectiveness[strategy_used].append(was_effective)
        
        # Limitar histórico
        for strategy in self.strategy_engine.strategy_effectiveness:
            history = self.strategy_engine.strategy_effectiveness[strategy]
            if len(history) > 50:
                self.strategy_engine.strategy_effectiveness[strategy] = history[-30:]
        
        logger.debug(f"AI adapted based on combat result: {combat_result}")
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da IA."""
        player_style = self.player_analyzer.get_player_style()
        
        return {
            "player_analysis": player_style,
            "actions_analyzed": len(self.player_analyzer.action_history),
            "strategies_tested": len(self.strategy_engine.strategy_effectiveness),
            "learning_enabled": self.learning_enabled,
            "most_effective_strategies": self._get_most_effective_strategies()
        }
    
    def _get_most_effective_strategies(self) -> List[Tuple[str, float]]:
        """Retorna estratégias mais efetivas."""
        effectiveness = []
        
        for strategy, results in self.strategy_engine.strategy_effectiveness.items():
            if results:
                avg_effectiveness = sum(results) / len(results)
                effectiveness.append((strategy, avg_effectiveness))
        
        return sorted(effectiveness, key=lambda x: x[1], reverse=True)[:5]
