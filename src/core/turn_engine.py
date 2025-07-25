"""
Medieval Deck - Turn Engine Core - Enhanced for P2 Sprint

Sistema de turnos principal do jogo, gerenciando o fluxo entre jogador e inimigos.
P2: Enhanced with minimal turn logic, damage calculation, and state management.
"""

import logging
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..gameplay.deck import Card
    from ..enemies.smart_enemies import SmartEnemy

logger = logging.getLogger(__name__)


class GameState(Enum):
    """Estados possíveis do jogo."""
    MENU = "menu"
    PLAYER_TURN = "player_turn"
    ENEMY_TURN = "enemy_turn"
    GAME_OVER = "game_over"
    VICTORY = "victory"
    PAUSED = "paused"


class TurnPhase(Enum):
    """Fases dentro de um turno."""
    START = "start"
    DRAW = "draw"
    MAIN = "main"
    COMBAT = "combat"
    END = "end"


class Player:
    """
    Classe base para o jogador - Enhanced for P2.
    
    Attributes:
        hp: Pontos de vida
        max_hp: HP máximo
        mana: Mana atual
        max_mana: Mana máximo
        deck: Referência ao deck do jogador
        hand: Cartas na mão
    """
    
    def __init__(self, max_hp: int = 30, max_mana: int = 10):
        self.max_hp = max_hp
        self.hp = max_hp
        self.max_mana = max_mana
        self.mana = max_mana
        self.deck = None  # Will be set by deck system
        self.hand = []
        self.is_alive = True
        
    def take_damage(self, damage: int) -> int:
        """
        Aplica dano ao jogador.
        
        Args:
            damage: Quantidade de dano
            
        Returns:
            Dano realmente aplicado
        """
        actual_damage = min(damage, self.hp)
        self.hp -= actual_damage
        
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
            logger.info("Player defeated!")
            
        logger.debug(f"Player took {actual_damage} damage. HP: {self.hp}/{self.max_hp}")
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        Cura o jogador.
        
        Args:
            amount: Quantidade de cura
            
        Returns:
            Cura realmente aplicada
        """
        actual_heal = min(amount, self.max_hp - self.hp)
        self.hp += actual_heal
        logger.debug(f"Player healed {actual_heal}. HP: {self.hp}/{self.max_hp}")
        return actual_heal
    
    def spend_mana(self, cost: int) -> bool:
        """
        Gasta mana do jogador.
        
        Args:
            cost: Custo de mana
            
        Returns:
            True se o mana foi gasto com sucesso
        """
        if self.mana >= cost:
            self.mana -= cost
            logger.debug(f"Player spent {cost} mana. Mana: {self.mana}/{self.max_mana}")
            return True
        return False
    
    def restore_mana(self, amount: int) -> int:
        """
        Restaura mana do jogador.
        
        Args:
            amount: Quantidade de mana a restaurar
            
        Returns:
            Mana realmente restaurado
        """
        actual_restore = min(amount, self.max_mana - self.mana)
        self.mana += actual_restore
        logger.debug(f"Player restored {actual_restore} mana. Mana: {self.mana}/{self.max_mana}")
        return actual_restore


class Enemy:
    """
    Classe base para inimigos.
    
    Attributes:
        name: Nome do inimigo
        hp: Pontos de vida
        max_hp: HP máximo
        attack: Poder de ataque base
        defense: Defesa base
        is_alive: Se o inimigo está vivo
    """
    
    def __init__(self, name: str, max_hp: int, attack: int, defense: int = 0):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.attack = attack
        self.defense = defense
        self.is_alive = True
        self.buffs = {}  # Buffs temporários
        
    def take_damage(self, damage: int) -> int:
        """
        Aplica dano ao inimigo, considerando defesa.
        
        Args:
            damage: Dano base
            
        Returns:
            Dano realmente aplicado
        """
        # Aplicar defesa
        reduced_damage = max(1, damage - self.defense)
        actual_damage = min(reduced_damage, self.hp)
        
        self.hp -= actual_damage
        
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
            logger.info(f"Enemy {self.name} defeated!")
            
        logger.debug(f"{self.name} took {actual_damage} damage. HP: {self.hp}/{self.max_hp}")
        return actual_damage
    
    def get_action(self) -> Dict[str, Any]:
        """
        Determina a próxima ação do inimigo.
        Por enquanto, ação simples de ataque.
        
        Returns:
            Dicionário com a ação a ser executada
        """
        # Implementação básica - sempre ataca
        return {
            "type": "attack",
            "target": "player",
            "damage": self.attack
        }


class TurnEngine:
    """
    Engine principal de turnos do Medieval Deck.
    
    Gerencia o fluxo do jogo entre turnos do jogador e inimigos,
    mantém o estado do jogo e coordena as ações.
    """
    
    def __init__(self, player: Player, enemies: List[Enemy]):
        """
        Inicializa o engine de turnos.
        
        Args:
            player: Instância do jogador
            enemies: Lista de inimigos
        """
        self.player = player
        self.enemies = enemies
        self.game_state = GameState.MENU
        self.turn_phase = TurnPhase.START
        self.turn_count = 0
        self.is_running = False
        
        # Callbacks para eventos
        self.on_player_turn_start = None
        self.on_player_turn_end = None
        self.on_enemy_turn_start = None
        self.on_enemy_turn_end = None
        self.on_game_over = None
        self.on_victory = None
        
        logger.info("TurnEngine initialized")
        logger.info(f"Player HP: {player.hp}, Enemies: {len(enemies)}")
    
    def start(self) -> None:
        """
        Inicia o loop principal do jogo.
        """
        logger.info("🎮 Starting Medieval Deck turn-based combat!")
        self.is_running = True
        self.game_state = GameState.PLAYER_TURN
        self.turn_count = 1
        
        # Loop principal do jogo
        while self.is_running and not self.check_end():
            try:
                if self.game_state == GameState.PLAYER_TURN:
                    self.player_turn()
                elif self.game_state == GameState.ENEMY_TURN:
                    self.enemy_turns()
                    
            except Exception as e:
                logger.error(f"Error in game loop: {e}")
                break
                
        # Jogo terminou
        final_state = self.check_end()
        if final_state:
            self._handle_game_end(final_state)
    
    def player_turn(self) -> None:
        """
        Executa o turno do jogador.
        Implementa as fases: START -> DRAW -> MAIN -> END
        """
        logger.info(f"🛡️ Player Turn {self.turn_count}")
        
        # Callback de início do turno
        if self.on_player_turn_start:
            self.on_player_turn_start()
        
        # FASE START: Efeitos de início de turno
        self.turn_phase = TurnPhase.START
        self._player_turn_start_phase()
        
        # FASE DRAW: Comprar cartas
        self.turn_phase = TurnPhase.DRAW
        self._player_turn_draw_phase()
        
        # FASE MAIN: Jogador toma decisões
        self.turn_phase = TurnPhase.MAIN
        self._player_turn_main_phase()
        
        # FASE END: Finalizar turno
        self.turn_phase = TurnPhase.END
        self._player_turn_end_phase()
        
        # Callback de fim do turno
        if self.on_player_turn_end:
            self.on_player_turn_end()
        
        # Transição para turno dos inimigos
        self.game_state = GameState.ENEMY_TURN
    
    def enemy_turns(self) -> None:
        """
        Executa os turnos de todos os inimigos vivos.
        """
        logger.info("⚔️ Enemy Turns")
        
        # Callback de início dos turnos inimigos
        if self.on_enemy_turn_start:
            self.on_enemy_turn_start()
        
        # Cada inimigo vivo age
        for enemy in self.enemies:
            if enemy.is_alive:
                self._execute_enemy_action(enemy)
        
        # Callback de fim dos turnos inimigos
        if self.on_enemy_turn_end:
            self.on_enemy_turn_end()
        
        # Próximo turno do jogador
        self.turn_count += 1
        self.game_state = GameState.PLAYER_TURN
    
    def check_end(self) -> Optional[str]:
        """
        Verifica se o jogo deve terminar.
        
        Returns:
            'defeat' se jogador morreu, 'victory' se todos inimigos morreram, None caso contrário
        """
        if not self.player.is_alive:
            return 'defeat'
        
        if all(not enemy.is_alive for enemy in self.enemies):
            return 'victory'
        
        return None
    
    def stop(self) -> None:
        """
        Para o engine de turnos.
        """
        logger.info("Stopping TurnEngine")
        self.is_running = False
        self.game_state = GameState.MENU
    
    # ===== FASES DO TURNO DO JOGADOR =====
    
    def _player_turn_start_phase(self) -> None:
        """Fase START do turno do jogador."""
        # Restaurar mana (implementação básica)
        self.player.mana = self.player.max_mana
        logger.debug("Player mana restored to full")
    
    def _player_turn_draw_phase(self) -> None:
        """Fase DRAW do turno do jogador."""
        # Por enquanto, sem sistema de cartas implementado
        # TODO: Implementar quando deck system estiver pronto
        logger.debug("Draw phase (cards not implemented yet)")
    
    def _player_turn_main_phase(self) -> None:
        """
        Fase MAIN do turno do jogador.
        Aqui o jogador pode jogar cartas, atacar, etc.
        """
        # Por enquanto, implementação básica para teste
        # TODO: Integrar com sistema de cartas e UI
        logger.debug("Main phase - player can take actions")
        
        # Simulação: jogador sempre ataca o primeiro inimigo vivo
        for enemy in self.enemies:
            if enemy.is_alive:
                damage = 5  # Dano base do jogador
                enemy.take_damage(damage)
                logger.info(f"Player attacks {enemy.name} for {damage} damage")
                break
    
    def _player_turn_end_phase(self) -> None:
        """Fase END do turno do jogador."""
        # Aplicar efeitos de fim de turno
        # TODO: Implementar efeitos de cartas
        logger.debug("End phase")
    
    # ===== AÇÕES DOS INIMIGOS =====
    
    def _execute_enemy_action(self, enemy: Enemy) -> None:
        """
        Executa a ação de um inimigo.
        
        Args:
            enemy: Inimigo que vai agir
        """
        action = enemy.get_action()
        logger.info(f"{enemy.name} takes action: {action['type']}")
        
        if action["type"] == "attack":
            # Inimigo ataca o jogador
            damage = action["damage"]
            self.player.take_damage(damage)
            logger.info(f"{enemy.name} attacks player for {damage} damage")
    
    def _handle_game_end(self, result: str) -> None:
        """
        Lida com o fim do jogo.
        
        Args:
            result: 'victory' ou 'defeat'
        """
        if result == 'victory':
            logger.info("🎉 VICTORY! All enemies defeated!")
            self.game_state = GameState.VICTORY
            if self.on_victory:
                self.on_victory()
                
        elif result == 'defeat':
            logger.info("💀 DEFEAT! Player has fallen!")
            self.game_state = GameState.GAME_OVER
            if self.on_game_over:
                self.on_game_over()
    
    # ===== MÉTODOS UTILITÁRIOS =====
    
    def get_alive_enemies(self) -> List[Enemy]:
        """Retorna lista de inimigos vivos."""
        return [enemy for enemy in self.enemies if enemy.is_alive]
    
    def get_game_info(self) -> Dict[str, Any]:
        """
        Retorna informações do estado atual do jogo.
        
        Returns:
            Dicionário com informações do jogo
        """
        return {
            "turn_count": self.turn_count,
            "game_state": self.game_state.value,
            "turn_phase": self.turn_phase.value,
            "player_hp": f"{self.player.hp}/{self.player.max_hp}",
            "player_mana": f"{self.player.mana}/{self.player.max_mana}",
            "alive_enemies": len(self.get_alive_enemies()),
            "total_enemies": len(self.enemies)
        }
    
    # ===== P2 ENHANCED METHODS =====
    
    def player_turn_simple(self, card: 'Card', target_enemy: 'SmartEnemy') -> bool:
        """
        P2: Simplified player turn - play one card against enemy.
        
        Args:
            card: Card to play
            target_enemy: Enemy to target
            
        Returns:
            True if turn was successful
        """
        if not card or not target_enemy or not target_enemy.is_alive:
            return False
            
        try:
            # Apply card damage to enemy
            damage = getattr(card, 'damage', 0)
            if damage > 0:
                target_enemy.hp -= damage
                logger.info(f"Player plays {card.name}: {damage} damage to {target_enemy.name}")
                
                # Check if enemy died
                if target_enemy.hp <= 0:
                    target_enemy.hp = 0
                    logger.info(f"{target_enemy.name} defeated!")
                    
            # Apply card healing to player if it's a heal card
            heal_amount = getattr(card, 'heal', 0)
            if heal_amount > 0:
                old_hp = self.player.hp
                self.player.hp = min(self.player.max_hp, self.player.hp + heal_amount)
                actual_heal = self.player.hp - old_hp
                logger.info(f"Player heals for {actual_heal} HP")
                
            return True
            
        except Exception as e:
            logger.error(f"Error in player turn: {e}")
            return False
    
    def enemy_turn_simple(self) -> None:
        """
        P2: Simplified enemy turn - each alive enemy attacks player.
        """
        alive_enemies = self.get_alive_enemies()
        
        for enemy in alive_enemies:
            if not enemy.is_alive:
                continue
                
            try:
                # Basic enemy attack
                base_damage = getattr(enemy, 'attack', 3)  # Default 3 damage
                
                # Apply damage to player
                old_hp = self.player.hp
                self.player.hp = max(0, self.player.hp - base_damage)
                actual_damage = old_hp - self.player.hp
                
                logger.info(f"{enemy.name} attacks player for {actual_damage} damage")
                
                # Check if player died
                if self.player.hp <= 0:
                    self.player.hp = 0
                    logger.info("Player defeated!")
                    break
                    
            except Exception as e:
                logger.error(f"Error in enemy turn for {enemy.name}: {e}")
                
    def apply_damage(self, target, damage: int) -> int:
        """
        P2: Apply damage to a target and return actual damage dealt.
        
        Args:
            target: Target entity (player or enemy)
            damage: Damage amount
            
        Returns:
            Actual damage dealt
        """
        if damage <= 0:
            return 0
            
        old_hp = target.hp
        target.hp = max(0, target.hp - damage)
        actual_damage = old_hp - target.hp
        
        logger.debug(f"Applied {actual_damage} damage to {getattr(target, 'name', 'target')}")
        return actual_damage
        
    def apply_healing(self, target, heal_amount: int) -> int:
        """
        P2: Apply healing to a target and return actual healing done.
        
        Args:
            target: Target entity (usually player)
            heal_amount: Healing amount
            
        Returns:
            Actual healing done
        """
        if heal_amount <= 0:
            return 0
            
        old_hp = target.hp
        max_hp = getattr(target, 'max_hp', target.hp)
        target.hp = min(max_hp, target.hp + heal_amount)
        actual_heal = target.hp - old_hp
        
        logger.debug(f"Applied {actual_heal} healing to {getattr(target, 'name', 'target')}")
        return actual_heal
        
    def end_turn(self) -> None:
        """
        P2: End current turn and advance to next phase.
        """
        if self.game_state == GameState.PLAYER_TURN:
            # Switch to enemy turn
            self.game_state = GameState.ENEMY_TURN
            logger.info("Player turn ended, switching to enemy turn")
            
        elif self.game_state == GameState.ENEMY_TURN:
            # Switch to player turn
            self.game_state = GameState.PLAYER_TURN
            self.turn_count += 1
            logger.info(f"Enemy turn ended, starting player turn {self.turn_count}")
            
            # Refresh player mana for new turn
            self.player.mana = self.player.max_mana
    
    def is_game_over(self) -> bool:
        """P2: Quick check if game is over."""
        return self.check_end() is not None
