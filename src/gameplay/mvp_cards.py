"""
Medieval Deck - MVP Cards System

Sistema de cartas simplificado para o MVP:
- Strike (ataque)
- Guard (defesa) 
- Heal (cura)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class CardType(Enum):
    """Tipos de carta."""
    ATTACK = "attack"
    DEFENSE = "defense"
    HEAL = "heal"
    MAGIC = "magic"

@dataclass
class Card:
    """Carta básica do MVP."""
    id: str
    name: str
    mana_cost: int
    card_type: CardType
    damage: int = 0
    block: int = 0
    heal: int = 0
    description: str = ""
    
    def can_play(self, current_mana: int) -> bool:
        """Verifica se a carta pode ser jogada."""
        return current_mana >= self.mana_cost
    
    def get_color(self) -> str:
        """Retorna a cor tema da carta."""
        color_map = {
            CardType.ATTACK: "card_attack",
            CardType.DEFENSE: "card_defense",
            CardType.HEAL: "card_heal",
            CardType.MAGIC: "card_magic"
        }
        return color_map.get(self.card_type, "silver")

class MVPCards:
    """Catálogo de cartas do MVP."""
    
    @staticmethod
    def get_all_cards() -> Dict[str, Card]:
        """Retorna todas as cartas do MVP."""
        return {
            "strike": Card(
                id="strike",
                name="Strike",
                mana_cost=1,
                card_type=CardType.ATTACK,
                damage=8,
                description="Deal 8 damage."
            ),
            "guard": Card(
                id="guard", 
                name="Guard",
                mana_cost=1,
                card_type=CardType.DEFENSE,
                block=8,
                description="Gain 8 block."
            ),
            "heal": Card(
                id="heal",
                name="Heal",
                mana_cost=2,
                card_type=CardType.HEAL,
                heal=6,
                description="Restore 6 HP."
            )
        }
    
    @staticmethod
    def create_starter_deck() -> List[str]:
        """Cria o deck inicial do MVP."""
        deck = []
        
        # 5x Strike
        deck.extend(["strike"] * 5)
        
        # 5x Guard  
        deck.extend(["guard"] * 5)
        
        # 2x Heal
        deck.extend(["heal"] * 2)
        
        return deck

class Hand:
    """Mão do jogador."""
    
    def __init__(self, max_size: int = 5):
        self.cards: List[Card] = []
        self.max_size = max_size
        self.selected_card: Optional[Card] = None
    
    def add_card(self, card: Card) -> bool:
        """Adiciona uma carta à mão."""
        if len(self.cards) < self.max_size:
            self.cards.append(card)
            return True
        return False
    
    def remove_card(self, card: Card) -> bool:
        """Remove uma carta da mão."""
        if card in self.cards:
            self.cards.remove(card)
            if self.selected_card == card:
                self.selected_card = None
            return True
        return False
    
    def select_card(self, index: int) -> Optional[Card]:
        """Seleciona uma carta pelo índice."""
        if 0 <= index < len(self.cards):
            self.selected_card = self.cards[index]
            return self.selected_card
        return None
    
    def clear(self):
        """Limpa a mão."""
        self.cards.clear()
        self.selected_card = None
    
    def is_full(self) -> bool:
        """Verifica se a mão está cheia."""
        return len(self.cards) >= self.max_size
    
    def get_playable_cards(self, current_mana: int) -> List[Card]:
        """Retorna cartas que podem ser jogadas com a mana atual."""
        return [card for card in self.cards if card.can_play(current_mana)]
