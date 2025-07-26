"""
Medieval Deck - MVP Turn Engine

Sistema de turnos simplificado para o MVP.
"""

import logging
from typing import Optional, Callable, Dict, Any
from ..gameplay.mvp_cards import Card

class MVPPlayer:
    """Jogador simplificado para o MVP."""
    
    def __init__(self, max_hp: int = 50, max_mana: int = 3):
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.max_mana = max_mana
        self.current_mana = max_mana
        self.block = 0
        
    def reset_mana(self):
        """Reseta a mana para o máximo."""
        self.current_mana = self.max_mana
    
    def spend_mana(self, amount: int) -> bool:
        """Gasta mana. Retorna True se foi possível."""
        if self.current_mana >= amount:
            self.current_mana -= amount
            return True
        return False
    
    def take_damage(self, damage: int) -> int:
        """Recebe dano considerando block. Retorna dano real recebido."""
        effective_damage = max(0, damage - self.block)
        self.current_hp = max(0, self.current_hp - effective_damage)
        self.block = 0  # Block é consumido
        return effective_damage
    
    def heal(self, amount: int) -> int:
        """Cura HP. Retorna a quantidade realmente curada."""
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp
    
    def add_block(self, amount: int):
        """Adiciona block."""
        self.block += amount
    
    def is_alive(self) -> bool:
        """Verifica se o jogador está vivo."""
        return self.current_hp > 0

class MVPEnemy:
    """Inimigo simplificado para o MVP."""
    
    def __init__(self, name: str, hp: int, attack: int, enemy_type: str = "goblin"):
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.attack = attack
        self.enemy_type = enemy_type
        self.intent = "attack"  # Sempre ataca no MVP
    
    def take_damage(self, damage: int) -> int:
        """Recebe dano. Retorna dano real recebido."""
        old_hp = self.current_hp
        self.current_hp = max(0, self.current_hp - damage)
        return old_hp - self.current_hp
    
    def is_alive(self) -> bool:
        """Verifica se o inimigo está vivo."""
        return self.current_hp > 0
    
    def get_next_action(self) -> Dict[str, Any]:
        """Retorna a próxima ação do inimigo."""
        return {
            "type": "attack",
            "damage": self.attack,
            "description": f"{self.name} will attack for {self.attack} damage"
        }

class MVPTurnEngine:
    """Engine de turnos simplificada para o MVP."""
    
    def __init__(self, player: MVPPlayer, enemy: MVPEnemy):
        self.player = player
        self.enemy = enemy
        self.turn_count = 1
        self.player_turn = True
        self.logger = logging.getLogger(__name__)
        
        # Callbacks para efeitos visuais
        self.on_damage_dealt: Optional[Callable] = None
        self.on_healing: Optional[Callable] = None
        self.on_block_gained: Optional[Callable] = None
        self.on_turn_end: Optional[Callable] = None
    
    def play_card(self, card: Card) -> Dict[str, Any]:
        """Joga uma carta. Retorna resultado da ação."""
        if not self.player_turn:
            return {"success": False, "message": "Not player turn"}
        
        if not card.can_play(self.player.current_mana):
            return {"success": False, "message": "Not enough mana"}
        
        # Gastar mana
        self.player.spend_mana(card.mana_cost)
        
        result = {"success": True, "effects": []}
        
        # Aplicar efeitos da carta
        if card.damage > 0:
            damage_dealt = self.enemy.take_damage(card.damage)
            result["effects"].append({
                "type": "damage",
                "target": "enemy",
                "amount": damage_dealt,
                "original": card.damage
            })
            
            if self.on_damage_dealt:
                self.on_damage_dealt("enemy", damage_dealt)
            
            self.logger.info(f"Player dealt {damage_dealt} damage to {self.enemy.name}")
        
        if card.block > 0:
            self.player.add_block(card.block)
            result["effects"].append({
                "type": "block",
                "target": "player", 
                "amount": card.block
            })
            
            if self.on_block_gained:
                self.on_block_gained("player", card.block)
            
            self.logger.info(f"Player gained {card.block} block")
        
        if card.heal > 0:
            heal_amount = self.player.heal(card.heal)
            result["effects"].append({
                "type": "heal",
                "target": "player",
                "amount": heal_amount,
                "original": card.heal
            })
            
            if self.on_healing:
                self.on_healing("player", heal_amount)
            
            self.logger.info(f"Player healed for {heal_amount} HP")
        
        # Verificar se inimigo morreu
        if not self.enemy.is_alive():
            result["enemy_defeated"] = True
            self.logger.info(f"{self.enemy.name} defeated!")
        
        return result
    
    def end_player_turn(self) -> Dict[str, Any]:
        """Finaliza o turno do jogador e executa turno do inimigo."""
        if not self.player_turn:
            return {"success": False, "message": "Not player turn"}
        
        self.player_turn = False
        result = {"success": True, "enemy_action": None}
        
        # Turno do inimigo (se vivo)
        if self.enemy.is_alive():
            enemy_action = self.enemy.get_next_action()
            
            if enemy_action["type"] == "attack":
                damage_dealt = self.player.take_damage(enemy_action["damage"])
                enemy_action["actual_damage"] = damage_dealt
                
                if self.on_damage_dealt:
                    self.on_damage_dealt("player", damage_dealt)
                
                self.logger.info(f"{self.enemy.name} dealt {damage_dealt} damage to player")
            
            result["enemy_action"] = enemy_action
        
        # Verificar se jogador morreu
        if not self.player.is_alive():
            result["player_defeated"] = True
            self.logger.info("Player defeated!")
        
        # Próximo turno
        self.turn_count += 1
        self.player_turn = True
        self.player.reset_mana()
        
        if self.on_turn_end:
            self.on_turn_end(self.turn_count)
        
        self.logger.info(f"Turn {self.turn_count} started")
        
        return result
    
    def is_game_over(self) -> bool:
        """Verifica se o jogo acabou."""
        return not self.player.is_alive() or not self.enemy.is_alive()
    
    def get_winner(self) -> Optional[str]:
        """Retorna o vencedor ou None se jogo não acabou."""
        if not self.player.is_alive():
            return "enemy"
        elif not self.enemy.is_alive():
            return "player"
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do jogo."""
        return {
            "turn": self.turn_count,
            "player_turn": self.player_turn,
            "player": {
                "hp": self.player.current_hp,
                "max_hp": self.player.max_hp,
                "mana": self.player.current_mana,
                "max_mana": self.player.max_mana,
                "block": self.player.block
            },
            "enemy": {
                "name": self.enemy.name,
                "hp": self.enemy.current_hp,
                "max_hp": self.enemy.max_hp,
                "attack": self.enemy.attack,
                "type": self.enemy.enemy_type,
                "intent": self.enemy.intent
            },
            "game_over": self.is_game_over(),
            "winner": self.get_winner()
        }
