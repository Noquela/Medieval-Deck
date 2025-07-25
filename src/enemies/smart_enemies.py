"""
Medieval Deck - Sistema de Inimigos Inteligentes

Implementação da Fase 3 do roadmap:
- Enemy AI com comportamentos específicos
- Tipos de inimigos especializados  
- Sistema de dificuldade adaptativa
- Padrões de ataque e defesa
"""

import random
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from abc import ABC, abstractmethod

from ..core.turn_engine import Enemy
from ..gameplay.cards import Card, CreatureCard, SpellCard

logger = logging.getLogger(__name__)


class EnemyType(Enum):
    """Tipos de inimigos conforme roadmap."""
    GOBLIN = "goblin"        # Básico, rápido
    ORC = "orc"              # Médio, agressivo
    DRAGON = "dragon"        # Boss, poderoso
    SKELETON = "skeleton"    # Morto-vivo, resistente
    WIZARD = "wizard"        # Mágico, tricky


class AIBehavior(Enum):
    """Comportamentos de IA conforme roadmap."""
    AGGRESSIVE = "aggressive"    # Ataca sempre
    DEFENSIVE = "defensive"      # Defende e contra-ataca
    TACTICAL = "tactical"        # Estratégico, usa timing
    RANDOM = "random"           # Imprevisível
    ADAPTIVE = "adaptive"       # Adapta ao jogador


class DifficultyLevel(Enum):
    """Níveis de dificuldade."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    NIGHTMARE = "nightmare"


class SmartEnemy(Enemy):
    """
    Inimigo inteligente com comportamentos específicos.
    
    Extende a classe Enemy base com IA avançada conforme roadmap.
    """
    
    def __init__(
        self,
        name: str,
        max_hp: int,
        attack: int,
        defense: int = 0,
        enemy_type: EnemyType = EnemyType.GOBLIN,
        ai_behavior: AIBehavior = AIBehavior.AGGRESSIVE,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    ):
        super().__init__(name, max_hp, attack, defense)
        self.enemy_type = enemy_type
        self.ai_behavior = ai_behavior
        self.difficulty = difficulty
        
        # Stats específicos por tipo
        self._apply_type_bonuses()
        
        # IA state tracking
        self.player_hp_history = []  # Para IA adaptativa
        self.last_player_actions = []  # Últimas ações do jogador
        self.turns_since_last_attack = 0
        self.preferred_targets = []  # Alvos preferenciais
        
        # Habilidades especiais por tipo
        self.special_abilities = self._get_special_abilities()
        self.cooldowns = {}  # Cooldowns de habilidades
        self.buffs = {}  # Buffs temporários
        
        logger.info(f"Created {self.enemy_type.value} {self.name} with {self.ai_behavior.value} AI")
    
    def _apply_type_bonuses(self) -> None:
        """Aplica bônus específicos por tipo de inimigo."""
        bonuses = {
            EnemyType.GOBLIN: {"speed": 1, "evasion": 0.1},
            EnemyType.ORC: {"attack": 2, "hp": 5},
            EnemyType.DRAGON: {"attack": 5, "hp": 15, "fire_resistance": 0.5},
            EnemyType.SKELETON: {"hp": 8, "defense": 3, "poison_immunity": True},
            EnemyType.WIZARD: {"hp": -5, "attack": -1, "magic_power": 3}
        }
        
        if self.enemy_type in bonuses:
            bonus = bonuses[self.enemy_type]
            
            if "attack" in bonus:
                self.attack += bonus["attack"]
            if "hp" in bonus:
                self.max_hp += bonus["hp"]
                self.hp = self.max_hp
            if "defense" in bonus:
                self.defense += bonus["defense"]
            
            # Aplicar resistências e imunidades
            for key, value in bonus.items():
                if key not in ["attack", "hp", "defense"]:
                    setattr(self, key, value)
    
    def _get_special_abilities(self) -> List[str]:
        """Retorna habilidades especiais do inimigo."""
        abilities = {
            EnemyType.GOBLIN: ["quick_strike", "dodge"],
            EnemyType.ORC: ["berserker_rage", "intimidate"],
            EnemyType.DRAGON: ["fire_breath", "wing_attack", "treasure_hoard"],
            EnemyType.SKELETON: ["bone_armor", "life_drain"],
            EnemyType.WIZARD: ["magic_missile", "teleport", "counterspell"]
        }
        return abilities.get(self.enemy_type, [])
    
    def decide_action(self, player, player_creatures: List[CreatureCard] = None) -> Dict[str, Any]:
        """
        Decide qual ação tomar baseado na IA.
        
        Args:
            player: Player object
            player_creatures: Criaturas do jogador em campo
            
        Returns:
            Dicionário com ação decidida
        """
        if player_creatures is None:
            player_creatures = []
            
        # Atualizar histórico para IA adaptativa
        self.player_hp_history.append(player.hp)
        if len(self.player_hp_history) > 10:
            self.player_hp_history.pop(0)
        
        # Escolher ação baseada no comportamento
        if self.ai_behavior == AIBehavior.AGGRESSIVE:
            return self._aggressive_action(player, player_creatures)
        elif self.ai_behavior == AIBehavior.DEFENSIVE:
            return self._defensive_action(player, player_creatures)
        elif self.ai_behavior == AIBehavior.TACTICAL:
            return self._tactical_action(player, player_creatures)
        elif self.ai_behavior == AIBehavior.ADAPTIVE:
            return self._adaptive_action(player, player_creatures)
        else:  # RANDOM
            return self._random_action(player, player_creatures)
    
    def _aggressive_action(self, player, player_creatures: List[CreatureCard]) -> Dict[str, Any]:
        """IA agressiva - sempre ataca."""
        # Prioridade: jogador > criaturas fracas > criaturas fortes
        if not player_creatures or random.random() < 0.7:
            return {
                "type": "attack",
                "target": "player",
                "damage": self.attack
            }
        else:
            # Atacar criatura mais fraca
            weakest = min(player_creatures, key=lambda c: c.current_hp)
            return {
                "type": "attack",
                "target": weakest.name,
                "damage": self.attack
            }
    
    def _defensive_action(self, player, player_creatures: List[CreatureCard]) -> Dict[str, Any]:
        """IA defensiva - defende quando necessário."""
        # Se HP baixo, tentar se curar ou defender
        if self.hp <= self.max_hp * 0.3:
            if "life_drain" in self.special_abilities and self._can_use_ability("life_drain"):
                return self._use_special_ability("life_drain", "player")
            elif "bone_armor" in self.special_abilities and self._can_use_ability("bone_armor"):
                return self._use_special_ability("bone_armor", "self")
        
        # Atacar ameaças prioritárias
        if player_creatures:
            # Eliminar criaturas pequenas primeiro
            weak_creatures = [c for c in player_creatures if c.current_hp <= self.attack]
            if weak_creatures:
                target = weak_creatures[0]
                return {
                    "type": "attack",
                    "target": target.name,
                    "damage": self.attack
                }
        
        # Ataque padrão
        return self._aggressive_action(player, player_creatures)
    
    def _tactical_action(self, player, player_creatures: List[CreatureCard]) -> Dict[str, Any]:
        """IA tática - usa timing e estratégia."""
        # Analisar estado do jogo
        total_enemy_hp = sum(c.current_hp for c in player_creatures)
        player_threat = player.hp + total_enemy_hp
        
        # Se jogador tem muitas criaturas, usar AOE
        if len(player_creatures) >= 3 and "fire_breath" in self.special_abilities:
            if self._can_use_ability("fire_breath"):
                return self._use_special_ability("fire_breath", "all_creatures")
        
        # Se jogador tem criaturas fortes, focar nelas
        if player_creatures:
            strong_creatures = [c for c in player_creatures if c.attack >= 4]
            if strong_creatures:
                target = max(strong_creatures, key=lambda c: c.attack)
                return {
                    "type": "attack",
                    "target": target.name,
                    "damage": self.attack
                }
        
        # Timing para habilidades especiais
        if self.turns_since_last_attack >= 2 and "berserker_rage" in self.special_abilities:
            if self._can_use_ability("berserker_rage"):
                return self._use_special_ability("berserker_rage", "self")
        
        return self._aggressive_action(player, player_creatures)
    
    def _adaptive_action(self, player, player_creatures: List[CreatureCard]) -> Dict[str, Any]:
        """IA adaptativa - se adapta ao estilo do jogador."""
        # Analisar histórico do jogador
        if len(self.player_hp_history) >= 3:
            recent_damage = self.player_hp_history[-3] - player.hp
            
            # Se jogador está sendo agressivo, ser mais defensivo
            if recent_damage > 10:
                return self._defensive_action(player, player_creatures)
            
            # Se jogador está passivo, ser mais agressivo
            if recent_damage <= 0:
                return self._aggressive_action(player, player_creatures)
        
        # Comportamento padrão tático
        return self._tactical_action(player, player_creatures)
    
    def _random_action(self, player, player_creatures: List[CreatureCard]) -> Dict[str, Any]:
        """IA aleatória - imprevisível."""
        actions = []
        
        # Ataques possíveis
        actions.append(("attack_player", 0.4))
        if player_creatures:
            actions.append(("attack_creature", 0.3))
        
        # Habilidades especiais
        for ability in self.special_abilities:
            if self._can_use_ability(ability):
                actions.append((f"special_{ability}", 0.2))
        
        # Escolher ação aleatoriamente (com pesos)
        if actions:
            action_type = random.choices(
                [a[0] for a in actions],
                weights=[a[1] for a in actions]
            )[0]
            
            if action_type == "attack_player":
                return self._aggressive_action(player, [])
            elif action_type == "attack_creature":
                return self._aggressive_action(player, player_creatures)
            elif action_type.startswith("special_"):
                ability = action_type.replace("special_", "")
                target = "player" if random.random() > 0.5 else (player_creatures[0].name if player_creatures else "player")
                return self._use_special_ability(ability, target)
        
        # Fallback
        return self._aggressive_action(player, player_creatures)
    
    def _can_use_ability(self, ability: str) -> bool:
        """Verifica se pode usar habilidade especial."""
        if ability not in self.special_abilities:
            return False
        
        # Verificar cooldown
        if ability in self.cooldowns and self.cooldowns[ability] > 0:
            return False
        
        # Verificações específicas por habilidade
        ability_requirements = {
            "fire_breath": lambda: self.hp > self.max_hp * 0.5,
            "berserker_rage": lambda: self.hp <= self.max_hp * 0.6,
            "life_drain": lambda: self.hp < self.max_hp,
            "magic_missile": lambda: True,
            "teleport": lambda: self.hp <= self.max_hp * 0.3
        }
        
        if ability in ability_requirements:
            return ability_requirements[ability]()
        
        return True
    
    def _use_special_ability(self, ability: str, target) -> Dict[str, Any]:
        """Usa habilidade especial."""
        # Aplicar cooldown
        cooldown_map = {
            "fire_breath": 3,
            "berserker_rage": 4,
            "life_drain": 2,
            "magic_missile": 1,
            "teleport": 5,
            "bone_armor": 3,
            "quick_strike": 1
        }
        
        if ability in cooldown_map:
            self.cooldowns[ability] = cooldown_map[ability]
        
        logger.info(f"{self.name} uses {ability}!")
        
        return {
            "type": "special_ability",
            "ability": ability,
            "target": target,
            "user": self.name
        }
    
    def execute_action(self, action: Dict[str, Any]) -> bool:
        """
        Executa a ação decidida.
        
        Args:
            action: Ação a ser executada
            
        Returns:
            True se foi executada com sucesso
        """
        try:
            if action["type"] == "attack":
                target = action["target"]
                damage = action["damage"]
                
                logger.info(f"{self.name} attacks {target} for {damage} damage")
                self.turns_since_last_attack = 0
                return True
                
            elif action["type"] == "special_ability":
                return self._execute_special_ability(action)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to execute action {action}: {e}")
            return False
    
    def _execute_special_ability(self, action: Dict[str, Any]) -> bool:
        """Executa habilidade especial."""
        ability = action["ability"]
        target = action["target"]
        
        if ability == "fire_breath":
            logger.info(f"{self.name} breathes fire on {target}!")
            return True
            
        elif ability == "berserker_rage":
            # Aumenta ataque temporariamente
            self.buffs["attack_boost"] = 5
            self.attack += 5
            logger.info(f"{self.name} enters berserker rage! (+5 attack)")
            return True
            
        elif ability == "life_drain":
            logger.info(f"{self.name} drains life from {target}")
            return True
                
        elif ability == "magic_missile":
            logger.info(f"Magic missile hits {target}")
            return True
                
        elif ability == "bone_armor":
            self.buffs["defense_boost"] = 3
            self.defense += 3
            logger.info(f"{self.name} gains bone armor! (+3 defense)")
            return True
            
        elif ability == "quick_strike":
            logger.info(f"Quick strike hits {target}")
            # 30% chance de segundo ataque
            if random.random() < 0.3:
                logger.info(f"Quick strike bonus!")
            return True
        
        return False
    
    def on_turn_start(self) -> None:
        """Executado no início do turno."""
        # Reduzir cooldowns
        for ability in list(self.cooldowns.keys()):
            self.cooldowns[ability] -= 1
            if self.cooldowns[ability] <= 0:
                del self.cooldowns[ability]
        
        # Incrementar contador de turnos
        self.turns_since_last_attack += 1
        
        # Remover buffs temporários
        expired_buffs = []
        for buff, duration in self.buffs.items():
            if isinstance(duration, int):
                self.buffs[buff] -= 1
                if self.buffs[buff] <= 0:
                    expired_buffs.append(buff)
        
        for buff in expired_buffs:
            self._remove_buff(buff)
    
    def _remove_buff(self, buff: str) -> None:
        """Remove um buff temporário."""
        if buff == "attack_boost":
            boost = self.buffs.get(buff, 0)
            self.attack -= boost
            logger.info(f"{self.name} loses attack boost (-{boost})")
        elif buff == "defense_boost":
            boost = self.buffs.get(buff, 0)
            self.defense -= boost
            logger.info(f"{self.name} loses defense boost (-{boost})")
        
        if buff in self.buffs:
            del self.buffs[buff]
    
    def get_difficulty_multiplier(self) -> float:
        """Retorna multiplicador baseado na dificuldade."""
        multipliers = {
            DifficultyLevel.EASY: 0.8,
            DifficultyLevel.MEDIUM: 1.0,
            DifficultyLevel.HARD: 1.3,
            DifficultyLevel.NIGHTMARE: 1.6
        }
        return multipliers.get(self.difficulty, 1.0)
    
    def scale_to_difficulty(self) -> None:
        """Escala stats baseado na dificuldade."""
        multiplier = self.get_difficulty_multiplier()
        
        if multiplier != 1.0:
            self.max_hp = int(self.max_hp * multiplier)
            self.hp = self.max_hp
            self.attack = int(self.attack * multiplier)
            self.defense = int(self.defense * multiplier)
            
            logger.info(f"{self.name} scaled to {self.difficulty.value} difficulty (×{multiplier})")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte inimigo para dicionário."""
        base_dict = {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "is_alive": self.is_alive()
        }
        
        # Adicionar dados específicos da IA
        base_dict.update({
            "enemy_type": self.enemy_type.value,
            "ai_behavior": self.ai_behavior.value,
            "difficulty": self.difficulty.value,
            "special_abilities": self.special_abilities,
            "cooldowns": self.cooldowns,
            "buffs": self.buffs
        })
        
        return base_dict
    
    def __str__(self) -> str:
        return f"{self.name} ({self.enemy_type.value}) - {self.hp}/{self.max_hp} HP, {self.attack} ATK, AI: {self.ai_behavior.value}"


class EnemyFactory:
    """Factory para criar inimigos específicos conforme roadmap."""
    
    @staticmethod
    def create_goblin(difficulty: DifficultyLevel = DifficultyLevel.MEDIUM) -> SmartEnemy:
        """Cria um Goblin (inimigo básico)."""
        goblin = SmartEnemy(
            name="Goblin Scout",
            max_hp=12,
            attack=3,
            defense=1,
            enemy_type=EnemyType.GOBLIN,
            ai_behavior=AIBehavior.AGGRESSIVE,
            difficulty=difficulty
        )
        goblin.scale_to_difficulty()
        return goblin
    
    @staticmethod
    def create_orc(difficulty: DifficultyLevel = DifficultyLevel.MEDIUM) -> SmartEnemy:
        """Cria um Orc (inimigo médio)."""
        orc = SmartEnemy(
            name="Orc Berserker",
            max_hp=20,
            attack=5,
            defense=2,
            enemy_type=EnemyType.ORC,
            ai_behavior=AIBehavior.TACTICAL,
            difficulty=difficulty
        )
        orc.scale_to_difficulty()
        return orc
    
    @staticmethod
    def create_dragon(difficulty: DifficultyLevel = DifficultyLevel.HARD) -> SmartEnemy:
        """Cria um Dragão (boss)."""
        dragon = SmartEnemy(
            name="Ancient Red Dragon",
            max_hp=50,
            attack=8,
            defense=5,
            enemy_type=EnemyType.DRAGON,
            ai_behavior=AIBehavior.ADAPTIVE,
            difficulty=difficulty
        )
        dragon.scale_to_difficulty()
        return dragon
    
    @staticmethod
    def create_skeleton(difficulty: DifficultyLevel = DifficultyLevel.MEDIUM) -> SmartEnemy:
        """Cria um Esqueleto (morto-vivo)."""
        skeleton = SmartEnemy(
            name="Skeleton Warrior",
            max_hp=15,
            attack=4,
            defense=3,
            enemy_type=EnemyType.SKELETON,
            ai_behavior=AIBehavior.DEFENSIVE,
            difficulty=difficulty
        )
        skeleton.scale_to_difficulty()
        return skeleton
    
    @staticmethod
    def create_wizard(difficulty: DifficultyLevel = DifficultyLevel.HARD) -> SmartEnemy:
        """Cria um Mago inimigo (tricky)."""
        wizard = SmartEnemy(
            name="Dark Wizard",
            max_hp=18,
            attack=6,
            defense=1,
            enemy_type=EnemyType.WIZARD,
            ai_behavior=AIBehavior.TACTICAL,
            difficulty=difficulty
        )
        wizard.scale_to_difficulty()
        return wizard
    
    @staticmethod
    def create_encounter(
        encounter_type: str,
        difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    ) -> List[SmartEnemy]:
        """
        Cria um encontro com múltiplos inimigos.
        
        Args:
            encounter_type: Tipo do encontro
            difficulty: Nível de dificuldade
            
        Returns:
            Lista de inimigos
        """
        encounters = {
            "goblin_patrol": [
                EnemyFactory.create_goblin(difficulty),
                EnemyFactory.create_goblin(difficulty)
            ],
            "orc_warband": [
                EnemyFactory.create_orc(difficulty),
                EnemyFactory.create_goblin(difficulty),
                EnemyFactory.create_goblin(difficulty)
            ],
            "undead_horde": [
                EnemyFactory.create_skeleton(difficulty),
                EnemyFactory.create_skeleton(difficulty)
            ],
            "dragon_lair": [
                EnemyFactory.create_dragon(difficulty)
            ],
            "wizard_tower": [
                EnemyFactory.create_wizard(difficulty),
                EnemyFactory.create_skeleton(difficulty)
            ],
            "mixed_encounter": [
                EnemyFactory.create_orc(difficulty),
                EnemyFactory.create_goblin(difficulty),
                EnemyFactory.create_skeleton(difficulty)
            ]
        }
        
        return encounters.get(encounter_type, [EnemyFactory.create_goblin(difficulty)])


class DifficultyManager:
    """Gerencia a dificuldade adaptativa do jogo."""
    
    def __init__(self):
        self.player_wins = 0
        self.player_losses = 0
        self.current_difficulty = DifficultyLevel.MEDIUM
        self.encounters_completed = 0
        
    def adjust_difficulty(self, player_won: bool) -> DifficultyLevel:
        """
        Ajusta dificuldade baseado no desempenho do jogador.
        
        Args:
            player_won: Se o jogador venceu o último combate
            
        Returns:
            Novo nível de dificuldade
        """
        if player_won:
            self.player_wins += 1
        else:
            self.player_losses += 1
        
        self.encounters_completed += 1
        
        # Calcular taxa de vitória
        win_rate = self.player_wins / self.encounters_completed
        
        # Ajustar dificuldade baseado na taxa de vitória
        if win_rate > 0.8 and self.encounters_completed >= 3:
            # Jogador está vencendo muito - aumentar dificuldade
            if self.current_difficulty == DifficultyLevel.EASY:
                self.current_difficulty = DifficultyLevel.MEDIUM
            elif self.current_difficulty == DifficultyLevel.MEDIUM:
                self.current_difficulty = DifficultyLevel.HARD
            elif self.current_difficulty == DifficultyLevel.HARD:
                self.current_difficulty = DifficultyLevel.NIGHTMARE
                
        elif win_rate < 0.3 and self.encounters_completed >= 3:
            # Jogador está perdendo muito - diminuir dificuldade
            if self.current_difficulty == DifficultyLevel.NIGHTMARE:
                self.current_difficulty = DifficultyLevel.HARD
            elif self.current_difficulty == DifficultyLevel.HARD:
                self.current_difficulty = DifficultyLevel.MEDIUM
            elif self.current_difficulty == DifficultyLevel.MEDIUM:
                self.current_difficulty = DifficultyLevel.EASY
        
        logger.info(f"Difficulty adjusted to {self.current_difficulty.value} (Win rate: {win_rate:.2f})")
        return self.current_difficulty
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do gerenciador de dificuldade."""
        return {
            "wins": self.player_wins,
            "losses": self.player_losses,
            "encounters": self.encounters_completed,
            "win_rate": self.player_wins / max(1, self.encounters_completed),
            "current_difficulty": self.current_difficulty.value
        }
