"""
Medieval Deck - Sistema de Cartas

Implementação das classes de cartas conforme Fase 2 do roadmap:
- Card: classe base
- CreatureCard: criaturas com ataque e defesa
- SpellCard: magias com efeitos
- ArtifactCard: artefatos e relíquias
"""

import json
import logging
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class CardType(Enum):
    """Tipos de cartas disponíveis."""
    CREATURE = "creature"
    SPELL = "spell"
    ARTIFACT = "artifact"


class CreatureType(Enum):
    """Tipos de criaturas conforme roadmap."""
    TANK = "tank"          # Cavaleiro - alta defesa
    DPS = "dps"            # Assassino - alto dano
    SUPPORT = "support"    # Mago - buffs e cura


class SpellType(Enum):
    """Tipos de magias conforme roadmap."""
    AOE = "aoe"            # Área de efeito
    BUFF = "buff"          # Melhoramento
    DEBUFF = "debuff"      # Enfraquecimento
    DAMAGE = "damage"      # Dano direto
    HEAL = "heal"          # Cura


class ArtifactType(Enum):
    """Tipos de artefatos conforme roadmap."""
    RELIC = "relic"        # Passivo permanente
    CONSUMABLE = "consumable"  # Uso único


class Card:
    """
    Classe base para todas as cartas.
    
    Attributes:
        id: Identificador único da carta
        name: Nome da carta
        cost: Custo de mana
        description: Descrição dos efeitos
        card_type: Tipo da carta (creature, spell, artifact)
        rarity: Raridade (common, uncommon, rare, legendary)
    """
    
    def __init__(
        self, 
        card_id: str, 
        name: str, 
        cost: int, 
        description: str, 
        card_type: CardType,
        rarity: str = "common"
    ):
        self.id = card_id
        self.name = name
        self.cost = cost
        self.description = description
        self.card_type = card_type
        self.rarity = rarity
        self.in_play = False
        
    def can_play(self, player, targets: List[Any] = None) -> bool:
        """
        Verifica se a carta pode ser jogada.
        
        Args:
            player: Jogador que quer jogar a carta
            targets: Alvos selecionados (se necessário)
            
        Returns:
            True se a carta pode ser jogada
        """
        # Verificar se tem mana suficiente
        if player.mana < self.cost:
            return False
        
        # Verificações específicas por tipo serão implementadas nas subclasses
        return True
    
    def play(self, player, targets: List[Any] = None) -> bool:
        """
        Joga a carta.
        
        Args:
            player: Jogador que está jogando a carta
            targets: Alvos da carta (se necessário)
            
        Returns:
            True se a carta foi jogada com sucesso
        """
        if not self.can_play(player, targets):
            return False
        
        # Gastar mana
        if not player.spend_mana(self.cost):
            return False
        
        logger.info(f"Playing card: {self.name} (Cost: {self.cost})")
        
        # Implementação específica nas subclasses
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte carta para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "cost": self.cost,
            "description": self.description,
            "card_type": self.card_type.value,
            "rarity": self.rarity
        }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.cost} mana) - {self.card_type.value.title()}"


class CreatureCard(Card):
    """
    Carta de criatura com ataque, defesa e habilidades especiais.
    
    Implementa os tipos conforme roadmap:
    - Tank (Cavaleiro): alta defesa
    - DPS (Assassino): alto dano
    - Support (Mago): buffs e suporte
    """
    
    def __init__(
        self,
        card_id: str,
        name: str,
        cost: int,
        description: str,
        attack: int,
        defense: int,
        creature_type: CreatureType,
        rarity: str = "common",
        abilities: List[str] = None
    ):
        super().__init__(card_id, name, cost, description, CardType.CREATURE, rarity)
        self.attack = attack
        self.defense = defense
        self.creature_type = creature_type
        self.abilities = abilities or []
        self.current_hp = defense  # HP atual (pode ser diferente da defesa base)
        self.is_alive = True
        self.buffs = {}  # Buffs temporários
        
    def on_play(self, player, targets: List[Any] = None) -> bool:
        """
        Efeito executado quando a criatura entra em jogo.
        
        Args:
            player: Jogador que jogou a carta
            targets: Alvos selecionados
            
        Returns:
            True se o efeito foi executado com sucesso
        """
        logger.info(f"Creature {self.name} enters the battlefield")
        self.in_play = True
        
        # Efeitos específicos por tipo de criatura
        if self.creature_type == CreatureType.TANK:
            # Tanques podem dar defesa ao jogador
            if "taunt" in self.abilities:
                logger.info(f"{self.name} taunts enemies!")
                
        elif self.creature_type == CreatureType.SUPPORT:
            # Suporte pode curar ou dar buffs
            if "heal" in self.abilities:
                heal_amount = 3
                player.heal(heal_amount)
                logger.info(f"{self.name} heals player for {heal_amount}")
        
        return True
    
    def attack_target(self, target) -> int:
        """
        Ataca um alvo.
        
        Args:
            target: Alvo do ataque (jogador ou criatura)
            
        Returns:
            Dano causado
        """
        damage = self.attack
        
        # Aplicar buffs de ataque
        if "attack_buff" in self.buffs:
            damage += self.buffs["attack_buff"]
        
        # Aplicar dano
        actual_damage = target.take_damage(damage)
        logger.info(f"{self.name} attacks for {actual_damage} damage")
        
        return actual_damage
    
    def take_damage(self, damage: int) -> int:
        """
        Recebe dano.
        
        Args:
            damage: Quantidade de dano
            
        Returns:
            Dano realmente recebido
        """
        # Aplicar buffs defensivos
        if "defense_buff" in self.buffs:
            damage = max(1, damage - self.buffs["defense_buff"])
        
        actual_damage = min(damage, self.current_hp)
        self.current_hp -= actual_damage
        
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_alive = False
            self.in_play = False
            logger.info(f"Creature {self.name} has been destroyed!")
        
        logger.debug(f"{self.name} takes {actual_damage} damage. HP: {self.current_hp}/{self.defense}")
        return actual_damage
    
    def play(self, player, targets: List[Any] = None) -> bool:
        """
        Joga a carta de criatura.
        """
        if not super().play(player, targets):
            return False
        
        # Executar efeito de entrada
        return self.on_play(player, targets)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte criatura para dicionário."""
        data = super().to_dict()
        data.update({
            "attack": self.attack,
            "defense": self.defense,
            "creature_type": self.creature_type.value,
            "abilities": self.abilities,
            "current_hp": self.current_hp,
            "is_alive": self.is_alive
        })
        return data
    
    def __str__(self) -> str:
        return f"{self.name} ({self.cost}) - {self.attack}/{self.defense} {self.creature_type.value.title()}"


class SpellCard(Card):
    """
    Carta de magia com efeitos diversos.
    
    Implementa os tipos conforme roadmap:
    - AOE: Área de efeito
    - Buff: Melhoramentos
    - Debuff: Enfraquecimentos
    - Damage: Dano direto
    - Heal: Cura
    """
    
    def __init__(
        self,
        card_id: str,
        name: str,
        cost: int,
        description: str,
        spell_type: SpellType,
        effect_function: Optional[Callable] = None,
        effect_value: int = 0,
        rarity: str = "common"
    ):
        super().__init__(card_id, name, cost, description, CardType.SPELL, rarity)
        self.spell_type = spell_type
        self.effect_function = effect_function
        self.effect_value = effect_value
        
    def effect(self, player, targets: List[Any] = None) -> bool:
        """
        Executa o efeito da magia.
        
        Args:
            player: Jogador que jogou a magia
            targets: Alvos da magia
            
        Returns:
            True se o efeito foi executado com sucesso
        """
        if self.effect_function:
            return self.effect_function(player, targets, self.effect_value)
        
        # Efeitos padrão por tipo
        if self.spell_type == SpellType.DAMAGE:
            if targets:
                for target in targets:
                    target.take_damage(self.effect_value)
                    logger.info(f"{self.name} deals {self.effect_value} damage to {target}")
                return True
                
        elif self.spell_type == SpellType.HEAL:
            player.heal(self.effect_value)
            logger.info(f"{self.name} heals player for {self.effect_value}")
            return True
            
        elif self.spell_type == SpellType.AOE:
            # Dano em área para todos os inimigos
            if hasattr(player, 'game_engine'):
                enemies = player.game_engine.get_alive_enemies()
                for enemy in enemies:
                    enemy.take_damage(self.effect_value)
                logger.info(f"{self.name} deals {self.effect_value} AOE damage")
                return True
        
        return False
    
    def play(self, player, targets: List[Any] = None) -> bool:
        """
        Joga a carta de magia.
        """
        if not super().play(player, targets):
            return False
        
        # Executar efeito
        success = self.effect(player, targets)
        
        # Magias vão para o cemitério após uso
        if success:
            logger.info(f"Spell {self.name} resolves and goes to graveyard")
        
        return success
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte magia para dicionário."""
        data = super().to_dict()
        data.update({
            "spell_type": self.spell_type.value,
            "effect_value": self.effect_value
        })
        return data
    
    def __str__(self) -> str:
        return f"{self.name} ({self.cost}) - {self.spell_type.value.title()} Spell"


class ArtifactCard(Card):
    """
    Carta de artefato com efeitos passivos ou consumíveis.
    
    Implementa os tipos conforme roadmap:
    - Relic: Efeito passivo permanente
    - Consumable: Uso único
    """
    
    def __init__(
        self,
        card_id: str,
        name: str,
        cost: int,
        description: str,
        artifact_type: ArtifactType,
        effect_function: Optional[Callable] = None,
        rarity: str = "common"
    ):
        super().__init__(card_id, name, cost, description, CardType.ARTIFACT, rarity)
        self.artifact_type = artifact_type
        self.effect_function = effect_function
        self.is_active = False
        
    def activate(self, player, targets: List[Any] = None) -> bool:
        """
        Ativa o artefato.
        
        Args:
            player: Jogador que ativou
            targets: Alvos (se necessário)
            
        Returns:
            True se foi ativado com sucesso
        """
        if self.effect_function:
            success = self.effect_function(player, targets)
        else:
            success = True
        
        if success:
            self.is_active = True
            
            if self.artifact_type == ArtifactType.RELIC:
                logger.info(f"Relic {self.name} provides permanent effect")
                self.in_play = True  # Relíquias ficam em jogo
            else:
                logger.info(f"Consumable {self.name} is used up")
                self.in_play = False  # Consumíveis saem de jogo
        
        return success
    
    def play(self, player, targets: List[Any] = None) -> bool:
        """
        Joga o artefato.
        """
        if not super().play(player, targets):
            return False
        
        return self.activate(player, targets)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte artefato para dicionário."""
        data = super().to_dict()
        data.update({
            "artifact_type": self.artifact_type.value,
            "is_active": self.is_active
        })
        return data
    
    def __str__(self) -> str:
        return f"{self.name} ({self.cost}) - {self.artifact_type.value.title()} Artifact"


class CardFactory:
    """
    Factory para criar cartas a partir de configurações JSON.
    """
    
    @staticmethod
    def create_from_config(card_config: Dict[str, Any]) -> Card:
        """
        Cria uma carta a partir de configuração.
        
        Args:
            card_config: Dicionário com configuração da carta
            
        Returns:
            Instância da carta criada
        """
        card_type = CardType(card_config["card_type"])
        
        if card_type == CardType.CREATURE:
            return CreatureCard(
                card_id=card_config["id"],
                name=card_config["name"],
                cost=card_config["cost"],
                description=card_config["description"],
                attack=card_config["attack"],
                defense=card_config["defense"],
                creature_type=CreatureType(card_config["creature_type"]),
                rarity=card_config.get("rarity", "common"),
                abilities=card_config.get("abilities", [])
            )
            
        elif card_type == CardType.SPELL:
            return SpellCard(
                card_id=card_config["id"],
                name=card_config["name"],
                cost=card_config["cost"],
                description=card_config["description"],
                spell_type=SpellType(card_config["spell_type"]),
                effect_value=card_config.get("effect_value", 0),
                rarity=card_config.get("rarity", "common")
            )
            
        elif card_type == CardType.ARTIFACT:
            return ArtifactCard(
                card_id=card_config["id"],
                name=card_config["name"],
                cost=card_config["cost"],
                description=card_config["description"],
                artifact_type=ArtifactType(card_config["artifact_type"]),
                rarity=card_config.get("rarity", "common")
            )
        
        raise ValueError(f"Unknown card type: {card_type}")
    
    @staticmethod
    def load_cards_from_file(file_path: Path) -> Dict[str, Card]:
        """
        Carrega cartas de um arquivo JSON.
        
        Args:
            file_path: Caminho para o arquivo de cartas
            
        Returns:
            Dicionário com cartas carregadas {id: card}
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cards_data = json.load(f)
            
            cards = {}
            for card_config in cards_data.get("cards", []):
                card = CardFactory.create_from_config(card_config)
                cards[card.id] = card
            
            logger.info(f"Loaded {len(cards)} cards from {file_path}")
            return cards
            
        except Exception as e:
            logger.error(f"Failed to load cards from {file_path}: {e}")
            return {}


# Funções de efeito pré-definidas para magias comuns
def fireball_effect(player, targets: List[Any], damage: int) -> bool:
    """Efeito de bola de fogo - dano em área."""
    if hasattr(player, 'game_engine'):
        enemies = player.game_engine.get_alive_enemies()
        for enemy in enemies:
            enemy.take_damage(damage)
        logger.info(f"Fireball deals {damage} damage to all enemies")
        return True
    return False


def healing_potion_effect(player, targets: List[Any], heal_amount: int) -> bool:
    """Efeito de poção de cura."""
    player.heal(heal_amount)
    logger.info(f"Healing potion restores {heal_amount} HP")
    return True


def shield_buff_effect(player, targets: List[Any], defense_bonus: int) -> bool:
    """Efeito de escudo - aumenta defesa temporariamente."""
    # Implementar sistema de buffs no jogador
    if hasattr(player, 'buffs'):
        player.buffs['defense'] = player.buffs.get('defense', 0) + defense_bonus
        logger.info(f"Shield increases defense by {defense_bonus}")
        return True
    return False
