"""
Battle Engine
Implements the battle state machine and turn-based logic.
"""
from enum import Enum
from typing import Dict, Optional, Callable
from pokemon_loader import PokemonData
from damage_calculator import DamageCalculator, get_move_info


class BattleState(Enum):
    """Battle state machine states."""
    SETUP = "SETUP"
    WAITING_FOR_MOVE = "WAITING_FOR_MOVE"
    PROCESSING_TURN = "PROCESSING_TURN"
    GAME_OVER = "GAME_OVER"


class BattleEngine:
    """Manages the battle state and turn logic."""
    
    def __init__(self, seed: int, is_host: bool = True):
        """
        Initialize battle engine.
        
        Args:
            seed: Random seed for synchronized calculations
            is_host: True if this peer is the host (goes first)
        """
        self.state = BattleState.SETUP
        self.seed = seed
        self.is_host = is_host
        self.is_my_turn = is_host
        self.calculator = DamageCalculator(seed)
        
        # Pokemon data
        self.my_pokemon: Optional[PokemonData] = None
        self.opponent_pokemon: Optional[PokemonData] = None
        self.my_pokemon_name: Optional[str] = None
        self.opponent_pokemon_name: Optional[str] = None
        
        # Current HP
        self.my_current_hp: int = 0
        self.opponent_current_hp: int = 0
        
        # Stat boosts
        self.my_stat_boosts: Dict[str, int] = {}
        self.opponent_stat_boosts: Dict[str, int] = {}
        
        # Turn tracking
        self.current_sequence: int = 0
        self.current_move: Optional[str] = None
        self.my_calculation: Optional[Dict] = None
        self.opponent_calculation: Optional[Dict] = None
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_turn_complete: Optional[Callable] = None
    
    def setup_battle(self, my_pokemon: PokemonData, opponent_pokemon: PokemonData,
                    my_stat_boosts: Dict[str, int], opponent_stat_boosts: Dict[str, int]):
        """Initialize the battle with Pokemon data."""
        self.my_pokemon = my_pokemon
        self.opponent_pokemon = opponent_pokemon
        self.my_pokemon_name = my_pokemon.name
        self.opponent_pokemon_name = opponent_pokemon.name
        self.my_current_hp = my_pokemon.hp
        self.opponent_current_hp = opponent_pokemon.hp
        self.my_stat_boosts = my_stat_boosts.copy()
        self.opponent_stat_boosts = opponent_stat_boosts.copy()
        self.state = BattleState.WAITING_FOR_MOVE
        if self.on_state_change:
            self.on_state_change(self.state)
    
    def can_attack(self) -> bool:
        """Check if it's this peer's turn to attack."""
        return self.state == BattleState.WAITING_FOR_MOVE and self.is_my_turn
    
    def announce_attack(self, move_name: str) -> int:
        """
        Announce an attack move.
        
        Returns:
            Sequence number for the attack
        """
        if not self.can_attack():
            raise ValueError("Not your turn to attack")
        
        self.current_sequence += 1
        self.current_move = move_name
        self.state = BattleState.PROCESSING_TURN
        if self.on_state_change:
            self.on_state_change(self.state)
        
        return self.current_sequence
    
    def receive_attack_announce(self, move_name: str) -> int:
        """
        Receive an attack announcement from opponent.
        
        Returns:
            Sequence number for defense announce
        """
        if self.is_my_turn:
            raise ValueError("Received attack when it's my turn")
        
        self.current_sequence += 1
        self.current_move = move_name
        self.state = BattleState.PROCESSING_TURN
        if self.on_state_change:
            self.on_state_change(self.state)
        
        return self.current_sequence
    
    def calculate_turn(self, move_name: str, is_attacker: bool) -> Dict:
        """
        Calculate damage for the current turn.
        
        Args:
            move_name: Name of the move used
            is_attacker: True if calculating for the attacker
        
        Returns:
            Dictionary with calculation results
        """
        move_info = get_move_info(move_name)
        
        if is_attacker:
            attacker = self.my_pokemon
            defender = self.opponent_pokemon
            attacker_boosts = self.my_stat_boosts
            defender_boosts = self.opponent_stat_boosts
        else:
            attacker = self.opponent_pokemon
            defender = self.my_pokemon
            attacker_boosts = self.opponent_stat_boosts
            defender_boosts = self.my_stat_boosts
        
        damage, status_message = self.calculator.calculate_damage(
            attacker, defender, move_name, move_info['type'],
            move_info['power'], move_info['category'],
            attacker_boosts.copy(), defender_boosts.copy()
        )
        
        if is_attacker:
            new_defender_hp = self.calculator.apply_damage(
                self.opponent_current_hp, damage
            )
            new_attacker_hp = self.my_current_hp
        else:
            new_defender_hp = self.calculator.apply_damage(
                self.my_current_hp, damage
            )
            new_attacker_hp = self.opponent_current_hp
        
        calculation = {
            'attacker': attacker.name,
            'move_used': move_name,
            'remaining_health': new_attacker_hp,
            'damage_dealt': damage,
            'defender_hp_remaining': new_defender_hp,
            'status_message': status_message
        }
        
        if is_attacker:
            self.my_calculation = calculation
        else:
            self.opponent_calculation = calculation
        
        return calculation
    
    def apply_calculation(self, calculation: Dict, is_my_calculation: bool):
        """Apply a calculation result to the battle state."""
        if is_my_calculation:
            self.my_calculation = calculation
            # Apply damage
            if calculation['attacker'] == self.my_pokemon_name:
                self.opponent_current_hp = calculation['defender_hp_remaining']
            else:
                self.my_current_hp = calculation['defender_hp_remaining']
        else:
            self.opponent_calculation = calculation
            # Apply damage
            if calculation['attacker'] == self.opponent_pokemon_name:
                self.my_current_hp = calculation['defender_hp_remaining']
            else:
                self.opponent_current_hp = calculation['defender_hp_remaining']
    
    def check_calculations_match(self) -> bool:
        """Check if both calculations match."""
        if not self.my_calculation or not self.opponent_calculation:
            return False
        
        my = self.my_calculation
        opp = self.opponent_calculation
        
        return (my['attacker'] == opp['attacker'] and
                my['move_used'] == opp['move_used'] and
                my['damage_dealt'] == opp['damage_dealt'] and
                my['defender_hp_remaining'] == opp['defender_hp_remaining'])
    
    def confirm_calculation(self):
        """Confirm that calculations match and advance turn."""
        if not self.check_calculations_match():
            return False
        
        # Check for game over
        if self.my_current_hp <= 0:
            self.state = BattleState.GAME_OVER
            if self.on_state_change:
                self.on_state_change(self.state)
            return True
        
        if self.opponent_current_hp <= 0:
            self.state = BattleState.GAME_OVER
            if self.on_state_change:
                self.on_state_change(self.state)
            return True
        
        # Switch turns
        self.is_my_turn = not self.is_my_turn
        self.state = BattleState.WAITING_FOR_MOVE
        self.my_calculation = None
        self.opponent_calculation = None
        
        if self.on_state_change:
            self.on_state_change(self.state)
        
        if self.on_turn_complete:
            self.on_turn_complete()
        
        return True
    
    def get_winner(self) -> Optional[str]:
        """Get the winner if the game is over."""
        if self.state != BattleState.GAME_OVER:
            return None
        
        if self.my_current_hp <= 0:
            return self.opponent_pokemon_name
        elif self.opponent_current_hp <= 0:
            return self.my_pokemon_name
        
        return None

