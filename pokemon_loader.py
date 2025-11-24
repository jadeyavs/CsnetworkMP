"""
Pokemon Data Loader
Loads and provides access to Pokemon data from the CSV file.
"""
import csv
from typing import Dict, Optional, List


class PokemonData:
    """Represents a Pokemon with all its stats and attributes."""
    
    def __init__(self, row: Dict[str, str]):
        self.name = row['name']
        self.pokedex_number = int(row['pokedex_number'])
        self.hp = int(row['hp'])
        self.attack = int(row['attack'])
        self.defense = int(row['defense'])
        self.sp_attack = int(row['sp_attack'])
        self.sp_defense = int(row['sp_defense'])
        self.speed = int(row['speed'])
        self.type1 = row['type1'].lower()
        self.type2 = row['type2'].lower() if row['type2'] else None
        self.weight_kg = float(row['weight_kg']) if row['weight_kg'] else 0.0
        self.height_m = float(row['height_m']) if row['height_m'] else 0.0
        self.generation = int(row['generation'])
        self.is_legendary = int(row['is_legendary']) == 1
        
        # Type effectiveness multipliers
        self.against_bug = float(row['against_bug'])
        self.against_dark = float(row['against_dark'])
        self.against_dragon = float(row['against_dragon'])
        self.against_electric = float(row['against_electric'])
        self.against_fairy = float(row['against_fairy'])
        self.against_fight = float(row['against_fight'])
        self.against_fire = float(row['against_fire'])
        self.against_flying = float(row['against_flying'])
        self.against_ghost = float(row['against_ghost'])
        self.against_grass = float(row['against_grass'])
        self.against_ground = float(row['against_ground'])
        self.against_ice = float(row['against_ice'])
        self.against_normal = float(row['against_normal'])
        self.against_poison = float(row['against_poison'])
        self.against_psychic = float(row['against_psychic'])
        self.against_rock = float(row['against_rock'])
        self.against_steel = float(row['against_steel'])
        self.against_water = float(row['against_water'])
    
    def get_type_effectiveness(self, move_type: str) -> float:
        """Get the type effectiveness multiplier for a given move type."""
        type_map = {
            'bug': self.against_bug,
            'dark': self.against_dark,
            'dragon': self.against_dragon,
            'electric': self.against_electric,
            'fairy': self.against_fairy,
            'fighting': self.against_fight,
            'fire': self.against_fire,
            'flying': self.against_flying,
            'ghost': self.against_ghost,
            'grass': self.against_grass,
            'ground': self.against_ground,
            'ice': self.against_ice,
            'normal': self.against_normal,
            'poison': self.against_poison,
            'psychic': self.against_psychic,
            'rock': self.against_rock,
            'steel': self.against_steel,
            'water': self.against_water,
        }
        return type_map.get(move_type.lower(), 1.0)
    
    def to_dict(self) -> Dict:
        """Convert Pokemon data to dictionary for serialization."""
        return {
            'name': self.name,
            'pokedex_number': self.pokedex_number,
            'hp': self.hp,
            'attack': self.attack,
            'defense': self.defense,
            'sp_attack': self.sp_attack,
            'sp_defense': self.sp_defense,
            'speed': self.speed,
            'type1': self.type1,
            'type2': self.type2,
            'weight_kg': self.weight_kg,
            'height_m': self.height_m,
            'generation': self.generation,
            'is_legendary': self.is_legendary,
        }


class PokemonLoader:
    """Loads and manages Pokemon data from CSV."""
    
    def __init__(self, csv_path: str = 'pokemon.csv'):
        self.pokemon_dict: Dict[str, PokemonData] = {}
        self.pokemon_by_number: Dict[int, PokemonData] = {}
        self._load_csv(csv_path)
    
    def _load_csv(self, csv_path: str):
        """Load Pokemon data from CSV file."""
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pokemon = PokemonData(row)
                self.pokemon_dict[pokemon.name.lower()] = pokemon
                self.pokemon_by_number[pokemon.pokedex_number] = pokemon
    
    def get_pokemon(self, name: str) -> Optional[PokemonData]:
        """Get Pokemon by name (case-insensitive)."""
        return self.pokemon_dict.get(name.lower())
    
    def get_pokemon_by_number(self, number: int) -> Optional[PokemonData]:
        """Get Pokemon by Pokedex number."""
        return self.pokemon_by_number.get(number)
    
    def list_all_pokemon(self) -> List[str]:
        """Get list of all Pokemon names."""
        return list(self.pokemon_dict.keys())
    
    def search_pokemon(self, query: str) -> List[PokemonData]:
        """Search Pokemon by name (partial match, case-insensitive)."""
        query_lower = query.lower()
        return [p for name, p in self.pokemon_dict.items() if query_lower in name]

