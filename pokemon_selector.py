"""
Pokemon Selector
Interactive Pokemon selection interface with pagination and search.
"""
import os
from typing import Optional, List
from pokemon_loader import PokemonLoader, PokemonData


class PokemonSelector:
    """Interactive Pokemon selection interface."""
    
    def __init__(self, pokemon_loader: PokemonLoader):
        self.loader = pokemon_loader
        self.pokemon_list = sorted(self.loader.list_all_pokemon())
        self.items_per_page = 20
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_page(self, page: int, search_results: Optional[List[str]] = None):
        """Display a page of Pokemon."""
        if search_results is not None:
            pokemon_to_display = search_results
        else:
            pokemon_to_display = self.pokemon_list
        
        total_pages = (len(pokemon_to_display) + self.items_per_page - 1) // self.items_per_page
        start_idx = page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(pokemon_to_display))
        
        print("\n" + "=" * 60)
        print("POKEMON SELECTION")
        print("=" * 60)
        
        if search_results is not None:
            print(f"Search Results (Page {page + 1}/{total_pages}):")
        else:
            print(f"All Pokemon (Page {page + 1}/{total_pages}):")
        
        print("-" * 60)
        
        for i in range(start_idx, end_idx):
            pokemon_name = pokemon_to_display[i]
            pokemon = self.loader.get_pokemon(pokemon_name)
            if pokemon:
                type_str = pokemon.type1.capitalize()
                if pokemon.type2:
                    type_str += f"/{pokemon.type2.capitalize()}"
                print(f"  {i - start_idx + 1:2d}. {pokemon_name:20s} | Type: {type_str:15s} | HP: {pokemon.hp:3d} | Total: {pokemon.hp + pokemon.attack + pokemon.defense + pokemon.sp_attack + pokemon.sp_defense + pokemon.speed:3d}")
        
        print("-" * 60)
        print("\nCommands:")
        print("  - Type a Pokemon name to select it")
        print("  - Type 'next' or 'n' to go to next page")
        print("  - Type 'prev' or 'p' to go to previous page")
        print("  - Type 'search <name>' to search for Pokemon")
        print("  - Type 'list' to show all Pokemon again")
        print("  - Type 'quit' to exit")
        print()
    
    def select_pokemon(self) -> Optional[PokemonData]:
        """Interactive Pokemon selection with pagination."""
        page = 0
        search_results = None
        search_query = None
        
        while True:
            self.clear_screen()
            self.display_page(page, search_results)
            
            try:
                user_input = input("Enter Pokemon name or command: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() == 'quit':
                    return None
                
                elif user_input.lower() in ['next', 'n']:
                    total_pages = (len(search_results if search_results else self.pokemon_list) + self.items_per_page - 1) // self.items_per_page
                    if page < total_pages - 1:
                        page += 1
                    else:
                        print("\nAlready on last page. Press Enter to continue...")
                        input()
                    continue
                
                elif user_input.lower() in ['prev', 'p']:
                    if page > 0:
                        page -= 1
                    else:
                        print("\nAlready on first page. Press Enter to continue...")
                        input()
                    continue
                
                elif user_input.lower().startswith('search '):
                    query = user_input[7:].strip()
                    if query:
                        search_results = [p for p in self.pokemon_list if query.lower() in p.lower()]
                        search_query = query
                        page = 0
                        if not search_results:
                            print(f"\nNo Pokemon found matching '{query}'. Press Enter to continue...")
                            input()
                    continue
                
                elif user_input.lower() == 'list':
                    search_results = None
                    search_query = None
                    page = 0
                    continue
                
                # Try to find Pokemon by name
                pokemon = self.loader.get_pokemon(user_input)
                if pokemon:
                    self.clear_screen()
                    print("\n" + "=" * 60)
                    print(f"SELECTED: {pokemon.name.upper()}")
                    print("=" * 60)
                    print(f"  Pokedex Number: {pokemon.pokedex_number}")
                    print(f"  Type: {pokemon.type1.capitalize()}", end="")
                    if pokemon.type2:
                        print(f" / {pokemon.type2.capitalize()}")
                    else:
                        print()
                    print(f"  HP: {pokemon.hp}")
                    print(f"  Attack: {pokemon.attack}")
                    print(f"  Defense: {pokemon.defense}")
                    print(f"  Sp. Attack: {pokemon.sp_attack}")
                    print(f"  Sp. Defense: {pokemon.sp_defense}")
                    print(f"  Speed: {pokemon.speed}")
                    print(f"  Total: {pokemon.hp + pokemon.attack + pokemon.defense + pokemon.sp_attack + pokemon.sp_defense + pokemon.speed}")
                    if pokemon.is_legendary:
                        print(f"  Legendary: Yes")
                    print("=" * 60)
                    
                    confirm = input("\nConfirm selection? (y/n): ").strip().lower()
                    if confirm == 'y':
                        return pokemon
                    else:
                        continue
                else:
                    print(f"\nPokemon '{user_input}' not found. Press Enter to continue...")
                    input()
                    continue
            
            except KeyboardInterrupt:
                return None
            except Exception as e:
                print(f"\nError: {e}. Press Enter to continue...")
                input()

