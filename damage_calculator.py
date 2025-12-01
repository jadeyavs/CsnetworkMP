"""
Damage Calculator
Implements the synchronized damage calculation formula for PokeProtocol.
"""
import random
from typing import Dict, Tuple
from pokemon_loader import PokemonData


class DamageCalculator:
    """Calculates damage for Pokemon battles using the protocol formula."""
    
    def __init__(self, seed: int):
        """Initialize with a seed for synchronized random number generation."""
        self.random = random.Random(seed)
    
    def calculate_damage(self, attacker: PokemonData, defender: PokemonData,
                        move_name: str, move_type: str, base_power: float,
                        damage_category: str, attacker_stat_boosts: Dict[str, int],
                        defender_stat_boosts: Dict[str, int]) -> Tuple[int, str]:
        """
        Calculate damage dealt by an attack.
        
        Returns:
            Tuple of (damage_dealt, status_message)
        """
        # Determine which stats to use based on damage category
        if damage_category.lower() == 'physical':
            attacker_stat = attacker.attack
            defender_stat = defender.defense
        else:  # special
            attacker_stat = attacker.sp_attack
            defender_stat = defender.sp_defense
        
        # Apply stat boosts (if available)
        if damage_category.lower() == 'physical':
            # Physical moves don't use special attack/defense boosts
            pass
        else:  # special
            # Apply special attack boost if available
            if attacker_stat_boosts.get('special_attack_uses', 0) > 0:
                attacker_stat = int(attacker_stat * 1.5)  # 50% boost
                attacker_stat_boosts['special_attack_uses'] -= 1
            
            # Apply special defense boost if available
            if defender_stat_boosts.get('special_defense_uses', 0) > 0:
                defender_stat = int(defender_stat * 1.5)  # 50% boost
                defender_stat_boosts['special_defense_uses'] -= 1
        
        # Calculate type effectiveness
        # The CSV file already contains combined type effectiveness for dual-type Pokemon
        # For example, a Grass/Water Pokemon's "against_fire" value already accounts for both types
        type_effectiveness = defender.get_type_effectiveness(move_type)
        
        # Generate random factor (0.85 to 1.0)
        random_factor = self.random.uniform(0.85, 1.0)
        
        # Damage calculation formula
        # Damage = ((2 * Level / 5 + 2) * Power * AttackerStat / DefenderStat / 50 + 2) * TypeEffectiveness * RandomFactor
        # Assuming level 50 for simplicity (can be made configurable)
        level = 50
        damage = ((2 * level / 5 + 2) * base_power * attacker_stat / defender_stat / 50 + 2) * type_effectiveness * random_factor
        
        damage_dealt = int(damage)
        
        # Generate status message
        effectiveness_text = ""
        if type_effectiveness >= 2.0:
            effectiveness_text = " It was super effective!"
        elif type_effectiveness <= 0.5:
            effectiveness_text = " It's not very effective..."
        elif type_effectiveness == 0:
            effectiveness_text = " It had no effect!"
        
        status_message = f"{attacker.name} used {move_name}!{effectiveness_text}"
        
        return damage_dealt, status_message
    
    def apply_damage(self, current_hp: int, damage: int) -> int:
        """Apply damage to current HP, ensuring it doesn't go below 0."""
        return max(0, current_hp - damage)


# Move database - simplified for now, can be expanded
MOVE_DATABASE = {
    'thunderbolt': {'type': 'electric', 'power': 90.0, 'category': 'special'},
    'thunder': {'type': 'electric', 'power': 110.0, 'category': 'special'},
    'quick attack': {'type': 'normal', 'power': 40.0, 'category': 'physical'},
    'tackle': {'type': 'normal', 'power': 40.0, 'category': 'physical'},
    'ember': {'type': 'fire', 'power': 40.0, 'category': 'special'},
    'flamethrower': {'type': 'fire', 'power': 90.0, 'category': 'special'},
    'water gun': {'type': 'water', 'power': 40.0, 'category': 'special'},
    'water shuriken': {'type': 'water', 'power': 75.0, 'category': 'special'},
    'hydro pump': {'type': 'water', 'power': 110.0, 'category': 'special'},
    'vine whip': {'type': 'grass', 'power': 45.0, 'category': 'physical'},
    'solar beam': {'type': 'grass', 'power': 120.0, 'category': 'special'},
    'scratch': {'type': 'normal', 'power': 40.0, 'category': 'physical'},
    'bite': {'type': 'dark', 'power': 60.0, 'category': 'physical'},
}


def get_move_info(move_name: str) -> Dict[str, any]:
    """Get move information from the move database."""
    move_lower = move_name.lower()
    if move_lower in MOVE_DATABASE:
        return MOVE_DATABASE[move_lower].copy()
    # Default move if not found
    return {'type': 'normal', 'power': 40.0, 'category': 'physical'}

