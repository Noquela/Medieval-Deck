"""
Card management system for Medieval Deck.

Handles card loading, validation, and operations.
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import json

from ..models.card_models import Card, CardType, Rarity
from ..utils.config import Config
from ..utils.helpers import load_json

logger = logging.getLogger(__name__)


class CardManager:
    """
    Manages card collection, loading, and validation.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize card manager.
        
        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.cards: Dict[str, Card] = {}
        self.cards_by_type: Dict[CardType, List[Card]] = {
            card_type: [] for card_type in CardType
        }
        self.cards_by_rarity: Dict[Rarity, List[Card]] = {
            rarity: [] for rarity in Rarity
        }
        
        # Load cards from configuration
        self.load_cards()
        
        logger.info(f"Card Manager initialized with {len(self.cards)} cards")
        
    def load_cards(self) -> None:
        """Load cards from configuration file."""
        cards_config_path = self.config.get_cards_config_path()
        
        if not cards_config_path.exists():
            logger.warning(f"Cards config not found: {cards_config_path}")
            self._create_default_cards()
            return
            
        cards_data = load_json(cards_config_path)
        if not cards_data or "cards" not in cards_data:
            logger.warning("Invalid cards configuration")
            self._create_default_cards()
            return
            
        # Load cards from data
        for card_data in cards_data["cards"]:
            try:
                card = Card.from_dict(card_data)
                self.add_card(card)
            except Exception as e:
                logger.error(f"Failed to load card {card_data.get('id', 'unknown')}: {e}")
                
        logger.info(f"Loaded {len(self.cards)} cards from configuration")
        
    def _create_default_cards(self) -> None:
        """Create default cards if no configuration exists."""
        default_cards = [
            Card(
                id="knight_basic",
                name="Knight",
                type=CardType.CREATURE,
                cost=3,
                attack=3,
                defense=4,
                description="A valiant knight ready for battle.",
                rarity=Rarity.COMMON,
                background_prompt="heroic warrior portrait, red banners, high detail"
            ),
            Card(
                id="wizard_basic",
                name="Wizard",
                type=CardType.CREATURE,
                cost=4,
                attack=2,
                defense=3,
                description="A wise wizard wielding arcane magic.",
                rarity=Rarity.UNCOMMON,
                background_prompt="arcane wizard, purple and blue energy, mystical runes"
            ),
            Card(
                id="assassin_basic",
                name="Assassin",
                type=CardType.CREATURE,
                cost=2,
                attack=3,
                defense=1,
                description="A stealthy assassin striking from shadows.",
                rarity=Rarity.UNCOMMON,
                background_prompt="dark assassin, black hood, soft shadows, moody"
            )
        ]
        
        for card in default_cards:
            self.add_card(card)
            
        logger.info("Created default card set")
        
    def add_card(self, card: Card) -> None:
        """
        Add a card to the collection.
        
        Args:
            card: Card to add
        """
        self.cards[card.id] = card
        self.cards_by_type[card.type].append(card)
        self.cards_by_rarity[card.rarity].append(card)
        
    def get_card(self, card_id: str) -> Optional[Card]:
        """
        Get card by ID.
        
        Args:
            card_id: Card ID
            
        Returns:
            Card object or None if not found
        """
        return self.cards.get(card_id)
        
    def get_cards_by_type(self, card_type: CardType) -> List[Card]:
        """
        Get all cards of a specific type.
        
        Args:
            card_type: Type of cards to get
            
        Returns:
            List of cards of specified type
        """
        return self.cards_by_type.get(card_type, []).copy()
        
    def get_cards_by_rarity(self, rarity: Rarity) -> List[Card]:
        """
        Get all cards of a specific rarity.
        
        Args:
            rarity: Rarity of cards to get
            
        Returns:
            List of cards of specified rarity
        """
        return self.cards_by_rarity.get(rarity, []).copy()
        
    def get_all_cards(self) -> List[Card]:
        """Get all cards in collection."""
        return list(self.cards.values())
        
    def search_cards(self, query: str) -> List[Card]:
        """
        Search cards by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching cards
        """
        query_lower = query.lower()
        results = []
        
        for card in self.cards.values():
            if (query_lower in card.name.lower() or 
                query_lower in card.description.lower()):
                results.append(card)
                
        return results
        
    def validate_card(self, card: Card) -> List[str]:
        """
        Validate card data.
        
        Args:
            card: Card to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not card.id:
            errors.append("Card ID is required")
            
        if not card.name:
            errors.append("Card name is required")
            
        if card.cost < 0:
            errors.append("Card cost cannot be negative")
            
        if card.attack < 0:
            errors.append("Card attack cannot be negative")
            
        if card.defense < 0:
            errors.append("Card defense cannot be negative")
            
        return errors
        
    def get_cards_needing_backgrounds(self) -> List[Card]:
        """Get cards that need AI-generated backgrounds."""
        return [card for card in self.cards.values() if not card.has_background()]
        
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the card collection."""
        type_counts = {card_type.value: len(cards) 
                      for card_type, cards in self.cards_by_type.items()}
        rarity_counts = {rarity.value: len(cards) 
                        for rarity, cards in self.cards_by_rarity.items()}
        
        # Count cards with backgrounds
        cards_with_backgrounds = sum(1 for card in self.cards.values() if card.has_background())
        
        return {
            "total_cards": len(self.cards),
            "by_type": type_counts,
            "by_rarity": rarity_counts,
            "with_backgrounds": cards_with_backgrounds,
            "without_backgrounds": len(self.cards) - cards_with_backgrounds
        }
