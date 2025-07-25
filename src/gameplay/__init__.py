"""
Medieval Deck - Módulo de Gameplay

Implementação da Fase 2 do roadmap:
- Sistema de cartas (cards.py)
- Sistema de deck (deck.py)  
- Engine de gameplay principal (gameplay_engine.py)

Este módulo conecta o TurnEngine com o sistema de cartas para criar
a experiência completa de jogo conforme especificado no roadmap.
"""

from .cards import (
    Card, CreatureCard, SpellCard, ArtifactCard,
    CardType, CreatureType, SpellType, ArtifactType,
    CardFactory
)

from .deck import (
    Deck, Hand, DrawPile, DiscardPile, 
    DeckBuilder
)

from .gameplay_engine import (
    GameplayEngine, GameplayDemo
)

__all__ = [
    # Cards
    'Card', 'CreatureCard', 'SpellCard', 'ArtifactCard',
    'CardType', 'CreatureType', 'SpellType', 'ArtifactType',
    'CardFactory',
    
    # Deck System
    'Deck', 'Hand', 'DrawPile', 'DiscardPile',
    'DeckBuilder',
    
    # Gameplay Engine
    'GameplayEngine', 'GameplayDemo'
]
