"""
Medieval Deck - Sistema de Deck

Implementação do sistema de deck conforme Fase 2 do roadmap:
- Deck: baralho principal
- Hand: cartas na mão
- DrawPile: pilha de compra
- DiscardPile: cemitério
"""

import random
import logging
from typing import List, Optional, Dict, Any
from collections import deque

from .cards import Card, CardFactory

logger = logging.getLogger(__name__)


class Hand:
    """
    Mão do jogador - cartas que podem ser jogadas.
    
    Attributes:
        cards: Lista de cartas na mão
        max_size: Tamanho máximo da mão
    """
    
    def __init__(self, max_size: int = 7):
        self.cards: List[Card] = []
        self.max_size = max_size
        
    def add_card(self, card: Card) -> bool:
        """
        Adiciona uma carta à mão.
        
        Args:
            card: Carta a ser adicionada
            
        Returns:
            True se a carta foi adicionada com sucesso
        """
        if len(self.cards) >= self.max_size:
            logger.warning(f"Hand is full! Cannot add {card.name}")
            return False
        
        self.cards.append(card)
        logger.debug(f"Added {card.name} to hand. Hand size: {len(self.cards)}")
        return True
    
    def remove_card(self, card: Card) -> bool:
        """
        Remove uma carta da mão.
        
        Args:
            card: Carta a ser removida
            
        Returns:
            True se a carta foi removida com sucesso
        """
        if card in self.cards:
            self.cards.remove(card)
            logger.debug(f"Removed {card.name} from hand. Hand size: {len(self.cards)}")
            return True
        return False
    
    def play_card(self, card: Card, player, targets: List[Any] = None) -> bool:
        """
        Joga uma carta da mão.
        
        Args:
            card: Carta a ser jogada
            player: Jogador que está jogando
            targets: Alvos da carta
            
        Returns:
            True se a carta foi jogada com sucesso
        """
        if card not in self.cards:
            logger.warning(f"Card {card.name} not in hand!")
            return False
        
        # Tentar jogar a carta
        if card.play(player, targets):
            self.remove_card(card)
            return True
        
        return False
    
    def get_playable_cards(self, player) -> List[Card]:
        """
        Retorna cartas que podem ser jogadas.
        
        Args:
            player: Jogador para verificar recursos
            
        Returns:
            Lista de cartas jogáveis
        """
        return [card for card in self.cards if card.can_play(player)]
    
    def is_full(self) -> bool:
        """Verifica se a mão está cheia."""
        return len(self.cards) >= self.max_size
    
    def is_empty(self) -> bool:
        """Verifica se a mão está vazia."""
        return len(self.cards) == 0
    
    def clear(self) -> List[Card]:
        """
        Remove todas as cartas da mão.
        
        Returns:
            Lista de cartas removidas
        """
        cards = self.cards.copy()
        self.cards.clear()
        logger.debug("Hand cleared")
        return cards
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte mão para dicionário."""
        return {
            "cards": [card.to_dict() for card in self.cards],
            "size": len(self.cards),
            "max_size": self.max_size
        }
    
    def __len__(self) -> int:
        return len(self.cards)
    
    def __iter__(self):
        return iter(self.cards)


class DrawPile:
    """
    Pilha de compra - cartas que podem ser compradas.
    
    Attributes:
        cards: Deque de cartas (pilha)
    """
    
    def __init__(self):
        self.cards: deque[Card] = deque()
        
    def add_card(self, card: Card) -> None:
        """
        Adiciona uma carta ao topo da pilha.
        
        Args:
            card: Carta a ser adicionada
        """
        self.cards.append(card)
        logger.debug(f"Added {card.name} to draw pile. Size: {len(self.cards)}")
    
    def add_cards(self, cards: List[Card]) -> None:
        """
        Adiciona múltiplas cartas à pilha.
        
        Args:
            cards: Lista de cartas a serem adicionadas
        """
        for card in cards:
            self.add_card(card)
    
    def draw_card(self) -> Optional[Card]:
        """
        Compra uma carta do topo da pilha.
        
        Returns:
            Carta comprada ou None se a pilha estiver vazia
        """
        if self.cards:
            card = self.cards.pop()
            logger.debug(f"Drew {card.name} from pile. Remaining: {len(self.cards)}")
            return card
        
        logger.warning("Draw pile is empty!")
        return None
    
    def draw_cards(self, count: int) -> List[Card]:
        """
        Compra múltiplas cartas.
        
        Args:
            count: Número de cartas a comprar
            
        Returns:
            Lista de cartas compradas
        """
        drawn_cards = []
        for _ in range(count):
            card = self.draw_card()
            if card:
                drawn_cards.append(card)
            else:
                break
        
        return drawn_cards
    
    def shuffle(self) -> None:
        """Embaralha a pilha de compra."""
        cards_list = list(self.cards)
        random.shuffle(cards_list)
        self.cards = deque(cards_list)
        logger.info(f"Draw pile shuffled. Size: {len(self.cards)}")
    
    def peek_top(self, count: int = 1) -> List[Card]:
        """
        Olha as cartas do topo sem comprá-las.
        
        Args:
            count: Número de cartas para olhar
            
        Returns:
            Lista de cartas do topo
        """
        return list(self.cards)[-count:] if len(self.cards) >= count else list(self.cards)
    
    def is_empty(self) -> bool:
        """Verifica se a pilha está vazia."""
        return len(self.cards) == 0
    
    def clear(self) -> List[Card]:
        """
        Remove todas as cartas da pilha.
        
        Returns:
            Lista de cartas removidas
        """
        cards = list(self.cards)
        self.cards.clear()
        logger.debug("Draw pile cleared")
        return cards
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte pilha para dicionário."""
        return {
            "size": len(self.cards),
            "top_cards": [card.to_dict() for card in self.peek_top(3)]
        }
    
    def __len__(self) -> int:
        return len(self.cards)


class DiscardPile:
    """
    Cemitério - cartas já jogadas/descartadas.
    
    Attributes:
        cards: Lista de cartas descartadas
    """
    
    def __init__(self):
        self.cards: List[Card] = []
        
    def add_card(self, card: Card) -> None:
        """
        Adiciona uma carta ao cemitério.
        
        Args:
            card: Carta a ser descartada
        """
        self.cards.append(card)
        logger.debug(f"Discarded {card.name}. Graveyard size: {len(self.cards)}")
    
    def add_cards(self, cards: List[Card]) -> None:
        """
        Adiciona múltiplas cartas ao cemitério.
        
        Args:
            cards: Lista de cartas a serem descartadas
        """
        for card in cards:
            self.add_card(card)
    
    def remove_card(self, card: Card) -> bool:
        """
        Remove uma carta do cemitério (ex: ressurreição).
        
        Args:
            card: Carta a ser removida
            
        Returns:
            True se a carta foi removida com sucesso
        """
        if card in self.cards:
            self.cards.remove(card)
            logger.debug(f"Removed {card.name} from graveyard")
            return True
        return False
    
    def get_top_card(self) -> Optional[Card]:
        """
        Retorna a carta do topo do cemitério.
        
        Returns:
            Carta do topo ou None se vazio
        """
        return self.cards[-1] if self.cards else None
    
    def get_cards_by_type(self, card_type) -> List[Card]:
        """
        Retorna cartas de um tipo específico.
        
        Args:
            card_type: Tipo de carta procurado
            
        Returns:
            Lista de cartas do tipo especificado
        """
        return [card for card in self.cards if card.card_type == card_type]
    
    def shuffle_into_draw_pile(self, draw_pile: DrawPile) -> int:
        """
        Embaralha cemitério de volta na pilha de compra.
        
        Args:
            draw_pile: Pilha de compra para adicionar as cartas
            
        Returns:
            Número de cartas reembalhadas
        """
        count = len(self.cards)
        if count > 0:
            # Randomizar ordem
            shuffled_cards = self.cards.copy()
            random.shuffle(shuffled_cards)
            
            # Adicionar à pilha de compra
            for card in shuffled_cards:
                draw_pile.add_card(card)
            
            # Limpar cemitério
            self.cards.clear()
            
            logger.info(f"Shuffled {count} cards from graveyard back into draw pile")
        
        return count
    
    def is_empty(self) -> bool:
        """Verifica se o cemitério está vazio."""
        return len(self.cards) == 0
    
    def clear(self) -> List[Card]:
        """
        Remove todas as cartas do cemitério.
        
        Returns:
            Lista de cartas removidas
        """
        cards = self.cards.copy()
        self.cards.clear()
        logger.debug("Discard pile cleared")
        return cards
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte cemitério para dicionário."""
        return {
            "cards": [card.to_dict() for card in self.cards],
            "size": len(self.cards),
            "top_card": self.get_top_card().to_dict() if self.get_top_card() else None
        }
    
    def __len__(self) -> int:
        return len(self.cards)


class Deck:
    """
    Deck completo do jogador - gerencia todas as pilhas de cartas.
    
    Implementa o sistema conforme roadmap:
    - draw(): move carta do draw_pile para hand
    - play(): executa efeito e descarta
    - reembaralhar quando draw_pile vazio
    """
    
    def __init__(self, cards: List[Card] = None, hand_size: int = 7):
        """
        Inicializa o deck.
        
        Args:
            cards: Lista inicial de cartas
            hand_size: Tamanho máximo da mão
        """
        self.hand = Hand(hand_size)
        self.draw_pile = DrawPile()
        self.discard_pile = DiscardPile()
        
        # Adicionar cartas iniciais e embaralhar
        if cards:
            self.draw_pile.add_cards(cards)
            self.draw_pile.shuffle()
        
        logger.info(f"Deck initialized with {len(self.draw_pile)} cards")
    
    def draw(self, count: int = 1) -> List[Card]:
        """
        Compra cartas para a mão.
        
        Args:
            count: Número de cartas a comprar
            
        Returns:
            Lista de cartas compradas
        """
        drawn_cards = []
        
        for _ in range(count):
            # Se a pilha de compra estiver vazia, reembaralhar o cemitério
            if self.draw_pile.is_empty() and not self.discard_pile.is_empty():
                self._reshuffle_discard_pile()
            
            # Tentar comprar carta
            card = self.draw_pile.draw_card()
            if card is None:
                logger.warning("No more cards to draw!")
                break
            
            # Adicionar à mão se houver espaço
            if self.hand.add_card(card):
                drawn_cards.append(card)
            else:
                # Mão cheia - descartar a carta
                self.discard_pile.add_card(card)
                logger.warning(f"Hand full, discarding {card.name}")
        
        if drawn_cards:
            logger.info(f"Drew {len(drawn_cards)} cards")
        
        return drawn_cards
    
    def play_card(self, card: Card, player, targets: List[Any] = None) -> bool:
        """
        Joga uma carta da mão.
        
        Args:
            card: Carta a ser jogada
            player: Jogador que está jogando
            targets: Alvos da carta
            
        Returns:
            True se a carta foi jogada com sucesso
        """
        # Jogar carta da mão
        if self.hand.play_card(card, player, targets):
            # Cartas vão para o cemitério após serem jogadas
            # (exceto criaturas que ficam em campo)
            if not card.in_play:
                self.discard_pile.add_card(card)
            
            return True
        
        return False
    
    def discard_card(self, card: Card) -> bool:
        """
        Descarta uma carta da mão.
        
        Args:
            card: Carta a ser descartada
            
        Returns:
            True se a carta foi descartada com sucesso
        """
        if self.hand.remove_card(card):
            self.discard_pile.add_card(card)
            logger.info(f"Discarded {card.name}")
            return True
        return False
    
    def discard_hand(self) -> int:
        """
        Descarta toda a mão.
        
        Returns:
            Número de cartas descartadas
        """
        cards = self.hand.clear()
        self.discard_pile.add_cards(cards)
        logger.info(f"Discarded entire hand ({len(cards)} cards)")
        return len(cards)
    
    def _reshuffle_discard_pile(self) -> None:
        """
        Reembaralha o cemitério de volta na pilha de compra.
        """
        count = self.discard_pile.shuffle_into_draw_pile(self.draw_pile)
        if count > 0:
            self.draw_pile.shuffle()
            logger.info(f"Reshuffled {count} cards from discard pile")
    
    def get_hand_size(self) -> int:
        """Retorna o tamanho atual da mão."""
        return len(self.hand)
        
    def end_turn(self) -> int:
        """
        Sprint 2-b: End turn logic - discard hand and draw new card.
        
        Returns:
            Number of cards drawn
        """
        # Discard current hand
        discarded = self.discard_hand()
        logger.info(f"End turn: Discarded {discarded} cards")
        
        # Draw 1 new card for next turn
        drawn_cards = self.draw(1)
        logger.info(f"End turn: Drew {len(drawn_cards)} cards for next turn")
        
        return len(drawn_cards)
    
    def get_deck_size(self) -> int:
        """Retorna o tamanho total do deck."""
        return len(self.draw_pile) + len(self.hand) + len(self.discard_pile)
    
    def get_playable_cards(self, player) -> List[Card]:
        """
        Retorna cartas na mão que podem ser jogadas.
        
        Args:
            player: Jogador para verificar recursos
            
        Returns:
            Lista de cartas jogáveis
        """
        return self.hand.get_playable_cards(player)
    
    def add_card_to_hand(self, card: Card) -> bool:
        """
        Adiciona uma carta diretamente à mão.
        
        Args:
            card: Carta a ser adicionada
            
        Returns:
            True se foi adicionada com sucesso
        """
        return self.hand.add_card(card)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte deck para dicionário."""
        return {
            "hand": self.hand.to_dict(),
            "draw_pile": self.draw_pile.to_dict(),
            "discard_pile": self.discard_pile.to_dict(),
            "total_size": self.get_deck_size()
        }
    
    def __str__(self) -> str:
        return (f"Deck: {len(self.draw_pile)} draw, "
                f"{len(self.hand)} hand, "
                f"{len(self.discard_pile)} discard")


class DeckBuilder:
    """
    Construtor de decks - cria decks a partir de configurações.
    """
    
    @staticmethod
    def create_starter_deck(deck_type: str = "balanced") -> Deck:
        """
        Cria um deck inicial básico.
        
        Args:
            deck_type: Tipo do deck ("balanced", "aggressive", "control")
            
        Returns:
            Deck criado
        """
        from .cards import (
            CreatureCard, SpellCard, ArtifactCard,
            CreatureType, SpellType, ArtifactType
        )
        
        cards = []
        
        if deck_type == "balanced":
            # Deck balanceado conforme roadmap
            
            # Criaturas (12 cartas)
            # Tank - Cavaleiro
            for i in range(3):
                cards.append(CreatureCard(
                    f"knight_{i+1}", f"Knight Warrior {i+1}", 
                    cost=3, description="A brave knight", 
                    attack=2, defense=5, creature_type=CreatureType.TANK,
                    abilities=["taunt"]
                ))
            
            # DPS - Assassino
            for i in range(3):
                cards.append(CreatureCard(
                    f"assassin_{i+1}", f"Shadow Assassin {i+1}", 
                    cost=2, description="A swift assassin", 
                    attack=4, defense=2, creature_type=CreatureType.DPS
                ))
            
            # Support - Mago
            for i in range(3):
                cards.append(CreatureCard(
                    f"mage_{i+1}", f"Arcane Mage {i+1}", 
                    cost=4, description="A wise mage", 
                    attack=2, defense=3, creature_type=CreatureType.SUPPORT,
                    abilities=["heal"]
                ))
            
            # Grunt - Básico
            for i in range(3):
                cards.append(CreatureCard(
                    f"grunt_{i+1}", f"Militia {i+1}", 
                    cost=1, description="Basic fighter", 
                    attack=1, defense=1, creature_type=CreatureType.DPS
                ))
            
            # Magias (6 cartas)
            for i in range(2):
                cards.append(SpellCard(
                    f"fireball_{i+1}", f"Fireball {i+1}", 
                    cost=3, description="Deals damage to all enemies", 
                    spell_type=SpellType.AOE, effect_value=3
                ))
            
            for i in range(2):
                cards.append(SpellCard(
                    f"heal_{i+1}", f"Healing Light {i+1}", 
                    cost=2, description="Restore health", 
                    spell_type=SpellType.HEAL, effect_value=5
                ))
            
            for i in range(2):
                cards.append(SpellCard(
                    f"bolt_{i+1}", f"Lightning Bolt {i+1}", 
                    cost=1, description="Quick damage spell", 
                    spell_type=SpellType.DAMAGE, effect_value=3
                ))
            
            # Artefatos (2 cartas)
            cards.append(ArtifactCard(
                "health_potion", "Health Potion", 
                cost=1, description="Restore health instantly", 
                artifact_type=ArtifactType.CONSUMABLE
            ))
            
            cards.append(ArtifactCard(
                "magic_ring", "Ring of Power", 
                cost=3, description="Increases maximum mana", 
                artifact_type=ArtifactType.RELIC
            ))
        
        deck = Deck(cards)
        logger.info(f"Created {deck_type} starter deck with {len(cards)} cards")
        return deck
    
    @staticmethod
    def load_deck_from_config(config_path: str) -> Deck:
        """
        Carrega um deck de um arquivo de configuração.
        
        Args:
            config_path: Caminho para o arquivo de configuração
            
        Returns:
            Deck carregado
        """
        try:
            from pathlib import Path
            
            # Carregar cartas disponíveis
            cards_dict = CardFactory.load_cards_from_file(Path(config_path))
            
            # TODO: Implementar lógica de seleção de cartas para o deck
            # Por enquanto, usar todas as cartas disponíveis
            deck_cards = list(cards_dict.values())
            
            deck = Deck(deck_cards)
            logger.info(f"Loaded deck from config with {len(deck_cards)} cards")
            return deck
            
        except Exception as e:
            logger.error(f"Failed to load deck from config {config_path}: {e}")
            # Fallback para deck inicial
            return DeckBuilder.create_starter_deck()
    
    @staticmethod
    def validate_deck(deck: Deck) -> Dict[str, Any]:
        """
        Valida se um deck está dentro das regras.
        
        Args:
            deck: Deck a ser validado
            
        Returns:
            Dicionário com resultado da validação
        """
        total_cards = deck.get_deck_size()
        min_cards = 20
        max_cards = 40
        
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "total_cards": total_cards
        }
        
        # Verificar tamanho mínimo/máximo
        if total_cards < min_cards:
            result["valid"] = False
            result["errors"].append(f"Deck too small: {total_cards} < {min_cards}")
        elif total_cards > max_cards:
            result["valid"] = False
            result["errors"].append(f"Deck too large: {total_cards} > {max_cards}")
        
        # TODO: Adicionar mais validações (cartas duplicadas, custo de mana, etc.)
        
        return result
