"""
Medieval Deck - Módulo de Inimigos Inteligentes

Implementação da Fase 3 do roadmap:
- Inimigos com IA avançada e comportamentos específicos
- Sistema de dificuldade adaptativa
- Análise de padrões do jogador
- Combate inteligente e estratégico

Este módulo transforma combates simples em experiências desafiadoras
e adaptativas que respondem ao estilo de jogo do usuário.
"""

from .smart_enemies import (
    SmartEnemy, EnemyFactory, DifficultyManager,
    EnemyType, AIBehavior, DifficultyLevel
)

from .ai_system import (
    AIBehaviorSystem, PlayerAnalyzer, StrategyEngine, DecisionTree
)

from .intelligent_combat import (
    IntelligentCombatEngine, EncounterManager
)

__all__ = [
    # Smart Enemies
    'SmartEnemy', 'EnemyFactory', 'DifficultyManager',
    'EnemyType', 'AIBehavior', 'DifficultyLevel',
    
    # AI System
    'AIBehaviorSystem', 'PlayerAnalyzer', 'StrategyEngine', 'DecisionTree',
    
    # Intelligent Combat
    'IntelligentCombatEngine', 'EncounterManager'
]
