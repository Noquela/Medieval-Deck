"""
Deck management system for Medieval Deck.

Handles deck building, validation, and operations.
"""

import logging
from typing import List, Dict, Optional, Any
import random

from ..models.card_models import Deck, Card, CardType, Rarity
from .cards import CardManager
from ..utils.config import Config

logger = logging.getLogger(__name__)


class DeckManager:
    """
    Manages deck creation, validation, and operations.
    """
    
    def __init__(self, card_manager: CardManager, config: Optional[Config] = None):
        """
        Initialize deck manager.
        
        Args:
            card_manager: Card manager instance
            config: Configuration object
        """
        self.card_manager = card_manager
        self.config = config or Config()
        self.decks: Dict[str, Deck] = {}
        
        # Create default decks
        self._create_default_decks()
        
        logger.info("Deck Manager initialized")
        
    def _create_default_decks(self) -> None:
        """Create default decks for testing."""
        # Basic Warrior Deck
        warrior_deck = self.create_deck("Warrior's Might")
        all_cards = self.card_manager.get_all_cards()
        
        # Add cards to reach minimum deck size
        for _ in range(self.config.game.min_deck_size):
            card = random.choice(all_cards)
            warrior_deck.add_card(card)
            
        self.decks["warrior"] = warrior_deck
        
        # Basic Mage Deck
        mage_deck = self.create_deck("Arcane Power")
        for _ in range(self.config.game.min_deck_size):
            card = random.choice(all_cards)
            mage_deck.add_card(card)
            
        self.decks["mage"] = mage_deck
        
        logger.info("Created default decks")
        
    def create_deck(self, name: str) -> Deck:
        """
        Create a new empty deck.
        
        Args:
            name: Deck name
            
        Returns:
            New deck instance
        """
        return Deck(
            name=name,
            max_size=self.config.game.max_deck_size,
            min_size=self.config.game.min_deck_size
        )
        
    def add_deck(self, deck: Deck, deck_id: Optional[str] = None) -> str:
        """
        Add a deck to the collection.
        
        Args:
            deck: Deck to add
            deck_id: Optional deck ID (generated if not provided)
            
        Returns:
            Deck ID
        """
        if deck_id is None:
            deck_id = deck.name.lower().replace(" ", "_")
            
        # Ensure unique ID
        counter = 1
        original_id = deck_id
        while deck_id in self.decks:
            deck_id = f"{original_id}_{counter}"
            counter += 1
            
        self.decks[deck_id] = deck
        logger.info(f"Added deck: {deck.name} (ID: {deck_id})")
        return deck_id
        
    def get_deck(self, deck_id: str) -> Optional[Deck]:
        """
        Get deck by ID.
        
        Args:
            deck_id: Deck ID
            
        Returns:
            Deck or None if not found
        """
        return self.decks.get(deck_id)
        
    def get_all_decks(self) -> Dict[str, Deck]:
        """Get all decks."""
        return self.decks.copy()
        
    def validate_deck(self, deck: Deck) -> List[str]:
        """
        Validate deck composition.
        
        Args:
            deck: Deck to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check size requirements
        if len(deck.cards) < deck.min_size:
            errors.append(f"Deck too small: {len(deck.cards)}/{deck.min_size}")
            
        if len(deck.cards) > deck.max_size:
            errors.append(f"Deck too large: {len(deck.cards)}/{deck.max_size}")
            
        # Check card limits (typically 4 copies max)
        card_counts = deck.get_card_counts()
        max_copies = 4
        
        for card_id, count in card_counts.items():
            if count > max_copies:
                card = self.card_manager.get_card(card_id)
                card_name = card.name if card else card_id
                errors.append(f"Too many copies of {card_name}: {count}/{max_copies}")
                
        # Check mana curve (warn if too steep)
        mana_curve = deck.get_mana_curve()
        high_cost_cards = sum(count for cost, count in mana_curve.items() if cost >= 6)
        
        if high_cost_cards > len(deck.cards) * 0.3:  # More than 30% high cost
            errors.append("Mana curve too steep (too many expensive cards)")
            
        return errors
        
    def build_random_deck(self, name: str, theme: Optional[CardType] = None) -> Deck:
        """
        Build a random deck with optional theme.
        
        Args:
            name: Deck name
            theme: Optional card type theme
            
        Returns:
            Random deck
        """
        deck = self.create_deck(name)
        
        # Get cards for theme
        if theme:
            themed_cards = self.card_manager.get_cards_by_type(theme)
            other_cards = [card for card in self.card_manager.get_all_cards() 
                          if card.type != theme]
        else:
            themed_cards = []
            other_cards = self.card_manager.get_all_cards()
            
        # Build deck with theme preference
        target_size = self.config.game.min_deck_size
        
        # Add themed cards (60% if theme specified)
        if themed_cards:
            themed_count = int(target_size * 0.6)
            for _ in range(min(themed_count, len(themed_cards))):
                card = random.choice(themed_cards)
                deck.add_card(card)
                
        # Fill with other cards
        while len(deck.cards) < target_size and other_cards:
            card = random.choice(other_cards)
            deck.add_card(card)
            
        logger.info(f"Built random deck: {name} ({len(deck.cards)} cards)")
        return deck
        
    def build_balanced_deck(self, name: str) -> Deck:
        """
        Build a balanced deck with good mana curve.
        
        Args:
            name: Deck name
            
        Returns:
            Balanced deck
        """
        deck = self.create_deck(name)
        all_cards = self.card_manager.get_all_cards()
        
        # Target distribution by mana cost
        target_distribution = {
            0: 0.05,  # 5% - 0 cost
            1: 0.15,  # 15% - 1 cost
            2: 0.20,  # 20% - 2 cost
            3: 0.20,  # 20% - 3 cost
            4: 0.15,  # 15% - 4 cost
            5: 0.10,  # 10% - 5 cost
            6: 0.10,  # 10% - 6+ cost
            7: 0.05,  # 5% - 7+ cost
        }
        
        target_size = self.config.game.min_deck_size
        
        # Group cards by cost
        cards_by_cost = {}
        for card in all_cards:
            cost = min(card.cost, 7)  # Cap at 7 for distribution
            if cost not in cards_by_cost:
                cards_by_cost[cost] = []
            cards_by_cost[cost].append(card)
            
        # Add cards according to distribution
        for cost, percentage in target_distribution.items():
            target_count = int(target_size * percentage)
            available_cards = cards_by_cost.get(cost, [])
            
            for _ in range(min(target_count, len(available_cards))):
                if len(deck.cards) < target_size:
                    card = random.choice(available_cards)
                    deck.add_card(card)
                    
        # Fill remaining slots
        while len(deck.cards) < target_size and all_cards:
            card = random.choice(all_cards)
            deck.add_card(card)
            
        deck.shuffle()
        logger.info(f"Built balanced deck: {name} ({len(deck.cards)} cards)")
        return deck
        
    def copy_deck(self, deck: Deck, new_name: str) -> Deck:
        """
        Create a copy of a deck.
        
        Args:
            deck: Deck to copy
            new_name: Name for the copy
            
        Returns:
            Copied deck
        """
        new_deck = self.create_deck(new_name)
        
        for card in deck.cards:
            new_deck.add_card(card)
            
        # Copy metadata
        new_deck.metadata = deck.metadata.copy()
        
        return new_deck
        
    def get_deck_stats(self, deck: Deck) -> Dict[str, Any]:
        """
        Get detailed statistics for a deck.
        
        Args:
            deck: Deck to analyze
            
        Returns:
            Deck statistics
        """
        if not deck.cards:
            return {"empty": True}
            
        # Basic stats
        total_cards = len(deck.cards)
        mana_curve = deck.get_mana_curve()
        card_counts = deck.get_card_counts()
        
        # Type distribution
        type_counts = {}
        for card in deck.cards:
            card_type = card.type.value
            type_counts[card_type] = type_counts.get(card_type, 0) + 1
            
        # Rarity distribution
        rarity_counts = {}
        for card in deck.cards:
            rarity = card.rarity.value
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
            
        # Average stats
        avg_cost = sum(card.cost for card in deck.cards) / total_cards
        avg_attack = sum(card.attack for card in deck.cards) / total_cards
        avg_defense = sum(card.defense for card in deck.cards) / total_cards
        
        return {
            "total_cards": total_cards,
            "unique_cards": len(card_counts),
            "mana_curve": mana_curve,
            "type_distribution": type_counts,
            "rarity_distribution": rarity_counts,
            "average_cost": round(avg_cost, 1),
            "average_attack": round(avg_attack, 1),
            "average_defense": round(avg_defense, 1),
            "is_valid": len(self.validate_deck(deck)) == 0
        }
