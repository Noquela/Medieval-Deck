"""
Medieval Deck - MVP Deck System

Sistema de deck simplificado para o MVP.
"""

import random
from typing import List, Optional
from .mvp_cards import Card, MVPCards, Hand

class MVPDeck:
    """Deck simplificado para o MVP."""
    
    def __init__(self):
        self.draw_pile: List[str] = []
        self.discard_pile: List[str] = []
        self.hand = Hand(max_size=5)
        self.cards_catalog = MVPCards.get_all_cards()
        
        # Criar deck inicial
        self.draw_pile = MVPCards.create_starter_deck()
        self.shuffle()
    
    def shuffle(self):
        """Embaralha o deck de compra."""
        random.shuffle(self.draw_pile)
    
    def draw_card(self) -> Optional[Card]:
        """Compra uma carta."""
        # Se deck de compra vazio, embaralhar descarte
        if not self.draw_pile and self.discard_pile:
            self.draw_pile = self.discard_pile.copy()
            self.discard_pile.clear()
            self.shuffle()
        
        # Comprar carta
        if self.draw_pile:
            card_id = self.draw_pile.pop()
            card = self.cards_catalog[card_id]
            return card
        
        return None
    
    def draw_hand(self, size: int = 5) -> List[Card]:
        """Compra uma mão inicial."""
        self.hand.clear()
        drawn_cards = []
        
        for _ in range(size):
            if self.hand.is_full():
                break
                
            card = self.draw_card()
            if card:
                self.hand.add_card(card)
                drawn_cards.append(card)
        
        return drawn_cards
    
    def play_card(self, card: Card) -> bool:
        """Joga uma carta (remove da mão, adiciona ao descarte)."""
        if self.hand.remove_card(card):
            self.discard_pile.append(card.id)
            return True
        return False
    
    def discard_hand(self):
        """Descarta toda a mão."""
        for card in self.hand.cards:
            self.discard_pile.append(card.id)
        self.hand.clear()
    
    def end_turn(self) -> Optional[Card]:
        """Finaliza o turno: descarta mão e compra 1 carta."""
        self.discard_hand()
        return self.draw_card()
    
    def get_deck_info(self) -> dict:
        """Retorna informações sobre o deck."""
        return {
            "draw_pile_size": len(self.draw_pile),
            "discard_pile_size": len(self.discard_pile),
            "hand_size": len(self.hand.cards),
            "total_cards": len(self.draw_pile) + len(self.discard_pile) + len(self.hand.cards)
        }
