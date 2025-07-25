"""
Medieval Deck - Sistema de Gameplay Principal

Conecta TurnEngine com sistema de cartas para implementar Fase 2 do roadmap.
Gerencia a lógica completa do jogo de cartas.
"""

import logging
from typing import List, Optional, Dict, Any
from enum import Enum

from ..core.turn_engine import TurnEngine, Player, Enemy, GameState, TurnPhase
from .cards import Card, CreatureCard, SpellCard, ArtifactCard
from .deck import Deck, DeckBuilder

logger = logging.getLogger(__name__)


class GameplayEngine:
    """
    Engine principal do gameplay que conecta sistema de turnos com cartas.
    
    Implementa a Fase 2 do roadmap:
    - Integração TurnEngine + Cards + Deck
    - Lógica de jogo completa
    - Gerenciamento de estado do jogo
    """
    
    def __init__(self, player: Player, enemies: List[Enemy]):
        """
        Inicializa o engine de gameplay.
        
        Args:
            player: Jogador
            enemies: Lista de inimigos
        """
        self.turn_engine = TurnEngine(player, enemies)
        self.player = player
        self.enemies = enemies
        
        # Conectar o player ao game engine para acesso aos inimigos
        self.player.game_engine = self
        
        # Deck do jogador
        self.player_deck = DeckBuilder.create_starter_deck("balanced")
        
        # Estado de gameplay
        self.turn_count = 0
        self.cards_played_this_turn = 0
        self.max_cards_per_turn = 3
        
        logger.info("GameplayEngine initialized")
    
    def start_game(self) -> None:
        """Inicia o jogo."""
        logger.info("=== MEDIEVAL DECK GAME START ===")
        
        # Inicializar o jogo de turnos
        self.turn_engine.start()
        
        # Comprar mão inicial
        initial_hand_size = 5
        drawn = self.player_deck.draw(initial_hand_size)
        logger.info(f"Player draws initial hand of {len(drawn)} cards")
        
        # Iniciar primeiro turno
        self._start_new_turn()
    
    def _start_new_turn(self) -> None:
        """Inicia um novo turno."""
        self.turn_count += 1
        self.cards_played_this_turn = 0
        
        logger.info(f"\n=== TURN {self.turn_count} ===")
        
        # Comprar carta no início do turno (após o primeiro)
        if self.turn_count > 1:
            drawn = self.player_deck.draw(1)
            if drawn:
                logger.info(f"Player draws: {drawn[0].name}")
        
        # Restaurar mana do jogador
        self.player.restore_mana(self.player.max_mana)
        
        logger.info(f"Player Mana: {self.player.mana}/{self.player.max_mana}")
        logger.info(f"Hand size: {self.player_deck.get_hand_size()}")
        logger.info(f"Deck size: {len(self.player_deck.draw_pile)}")
    
    def get_playable_cards(self) -> List[Card]:
        """
        Retorna cartas que o jogador pode jogar agora.
        
        Returns:
            Lista de cartas jogáveis
        """
        # Verificar limite de cartas por turno
        if self.cards_played_this_turn >= self.max_cards_per_turn:
            return []
        
        return self.player_deck.get_playable_cards(self.player)
    
    def play_card(self, card: Card, targets: List[Any] = None) -> bool:
        """
        Joga uma carta do jogador.
        
        Args:
            card: Carta a ser jogada
            targets: Alvos da carta
            
        Returns:
            True se a carta foi jogada com sucesso
        """
        if card not in self.get_playable_cards():
            logger.warning(f"Cannot play {card.name} - not playable")
            return False
        
        # Jogar a carta
        if self.player_deck.play_card(card, self.player, targets):
            self.cards_played_this_turn += 1
            
            # Log da jogada
            logger.info(f"✅ {card.name} played! ({self.cards_played_this_turn}/{self.max_cards_per_turn} cards this turn)")
            
            # Verificar se há criaturas em jogo para o player
            if isinstance(card, CreatureCard) and card.in_play:
                if not hasattr(self.player, 'creatures'):
                    self.player.creatures = []
                self.player.creatures.append(card)
                logger.info(f"Creature {card.name} added to battlefield")
            
            return True
        
        return False
    
    def get_alive_enemies(self) -> List[Enemy]:
        """Retorna inimigos ainda vivos."""
        return [enemy for enemy in self.enemies if enemy.is_alive]
    
    def get_alive_player_creatures(self) -> List[CreatureCard]:
        """Retorna criaturas do jogador ainda vivas."""
        if not hasattr(self.player, 'creatures'):
            return []
        return [creature for creature in self.player.creatures if creature.is_alive]
    
    def player_turn_action(self, action_type: str, **kwargs) -> bool:
        """
        Executa uma ação do jogador durante seu turno.
        
        Args:
            action_type: Tipo de ação ("play_card", "attack", "end_turn")
            **kwargs: Argumentos específicos da ação
            
        Returns:
            True se a ação foi executada com sucesso
        """
        if self.turn_engine.turn_phase != TurnPhase.MAIN:
            logger.warning("Not player's turn!")
            return False
        
        if action_type == "play_card":
            card = kwargs.get("card")
            targets = kwargs.get("targets", [])
            return self.play_card(card, targets)
        
        elif action_type == "attack":
            attacker = kwargs.get("attacker")  # CreatureCard
            target = kwargs.get("target")      # Enemy ou CreatureCard
            
            if isinstance(attacker, CreatureCard) and attacker.is_alive:
                damage = attacker.attack_target(target)
                logger.info(f"{attacker.name} attacks {target} for {damage} damage")
                return True
        
        elif action_type == "end_turn":
            return self.end_player_turn()
        
        return False
    
    def end_player_turn(self) -> bool:
        """
        Termina o turno do jogador.
        
        Returns:
            True se o turno foi finalizado
        """
        logger.info("Player ends turn")
        
        # Verificar se o jogo já terminou
        if self.is_game_over():
            logger.info("Game already finished!")
            return True
        
        # Resetar contadores
        self.cards_played_this_turn = 0
        
        # Avançar para turnos dos inimigos se o jogo ainda estiver ativo
        if hasattr(self.turn_engine, 'on_player_turn_end') and self.turn_engine.on_player_turn_end:
            self.turn_engine.on_player_turn_end()
        
        # Executar turnos dos inimigos
        self._execute_enemy_turns()
        
        # Verificar condições de fim de jogo
        game_state = self.turn_engine.check_end()
        
        if game_state == GameState.VICTORY:
            logger.info("🎉 VICTORY! All enemies defeated!")
            return True
        elif game_state == GameState.GAME_OVER:
            logger.info("💀 GAME OVER! Player has been defeated!")
            return True
        elif game_state == GameState.PLAYER_TURN:
            # Continuar para próximo turno
            self._start_new_turn()
        
        return True
    
    def _execute_enemy_turns(self) -> None:
        """Executa turnos de todos os inimigos."""
        logger.info("\n--- Enemy Turns ---")
        
        alive_enemies = self.get_alive_enemies()
        
        for enemy in alive_enemies:
            if not enemy.is_alive:
                continue
            
            logger.info(f"{enemy.name}'s turn")
            
            # IA simples do inimigo
            self._enemy_ai_turn(enemy)
        
        logger.info("--- End Enemy Turns ---\n")
    
    def _enemy_ai_turn(self, enemy: Enemy) -> None:
        """
        IA simples para turno do inimigo.
        
        Args:
            enemy: Inimigo que está jogando
        """
        # IA básica: atacar jogador ou criaturas do jogador
        player_creatures = self.get_alive_player_creatures()
        
        if player_creatures:
            # Atacar criatura mais fraca
            target = min(player_creatures, key=lambda c: c.current_hp)
            damage = enemy.attack(target)
            logger.info(f"{enemy.name} attacks {target.name} for {damage} damage")
            
            # Remover criatura se morreu
            if not target.is_alive:
                self.player.creatures.remove(target)
                logger.info(f"{target.name} is destroyed!")
        else:
            # Atacar jogador diretamente
            damage = enemy.attack(self.player)
            logger.info(f"{enemy.name} attacks player for {damage} damage")
    
    def get_game_state(self) -> Dict[str, Any]:
        """
        Retorna o estado atual do jogo.
        
        Returns:
            Dicionário com estado completo
        """
        return {
            "turn_count": self.turn_count,
            "current_phase": self.turn_engine.turn_phase.value,
            "game_state": self.turn_engine.game_state.value,
            "player": {
                "hp": self.player.hp,
                "max_hp": self.player.max_hp,
                "mana": self.player.mana,
                "max_mana": self.player.max_mana,
                "creatures": [c.to_dict() for c in self.get_alive_player_creatures()]
            },
            "enemies": [
                {
                    "name": enemy.name,
                    "hp": enemy.hp,
                    "max_hp": enemy.max_hp,
                    "alive": enemy.is_alive
                }
                for enemy in self.enemies
            ],
            "deck": self.player_deck.to_dict(),
            "playable_cards": [card.to_dict() for card in self.get_playable_cards()],
            "cards_played_this_turn": self.cards_played_this_turn,
            "max_cards_per_turn": self.max_cards_per_turn
        }
    
    def save_game_state(self, file_path: str) -> bool:
        """
        Salva o estado do jogo em arquivo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se salvou com sucesso
        """
        try:
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.get_game_state(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Game state saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save game state: {e}")
            return False
    
    def is_game_over(self) -> bool:
        """Verifica se o jogo terminou."""
        return self.turn_engine.game_state in [GameState.VICTORY, GameState.GAME_OVER]
    
    def get_victory_condition(self) -> Optional[str]:
        """
        Retorna a condição de vitória/derrota.
        
        Returns:
            String descrevendo como o jogo terminou
        """
        if self.turn_engine.game_state == GameState.VICTORY:
            return "All enemies defeated!"
        elif self.turn_engine.game_state == GameState.GAME_OVER:
            return "Player defeated!"
        else:
            return None


class GameplayDemo:
    """
    Demonstração do sistema de gameplay completo.
    """
    
    @staticmethod
    def run_demo() -> None:
        """Executa uma demonstração do gameplay."""
        logger.info("=== GAMEPLAY DEMO START ===")
        
        # Criar jogador
        player = Player("Hero", hp=30, mana=10)
        
        # Criar inimigos
        enemies = [
            Enemy("Goblin Warrior", hp=15, attack=3),
            Enemy("Orc Berserker", hp=20, attack=5)
        ]
        
        # Inicializar gameplay
        gameplay = GameplayEngine(player, enemies)
        gameplay.start_game()
        
        # Demonstrar algumas jogadas
        logger.info("\n--- Demo Plays ---")
        
        # Mostrar cartas na mão
        playable = gameplay.get_playable_cards()
        logger.info(f"Playable cards: {[card.name for card in playable]}")
        
        # Jogar algumas cartas
        if playable:
            # Jogar primeira carta jogável
            card = playable[0]
            targets = gameplay.get_alive_enemies() if isinstance(card, SpellCard) else None
            
            success = gameplay.player_turn_action("play_card", card=card, targets=targets)
            logger.info(f"Played {card.name}: {'Success' if success else 'Failed'}")
        
        # Mostrar estado do jogo
        state = gameplay.get_game_state()
        logger.info(f"Game State: {state['game_state']}")
        logger.info(f"Player HP: {state['player']['hp']}/{state['player']['max_hp']}")
        logger.info(f"Player Mana: {state['player']['mana']}/{state['player']['max_mana']}")
        
        # Terminar turno
        gameplay.end_player_turn()
        
        logger.info("=== GAMEPLAY DEMO END ===")


if __name__ == "__main__":
    # Configurar logging para demo
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    GameplayDemo.run_demo()
