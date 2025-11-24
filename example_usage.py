"""
Example usage of PokeProtocol
This demonstrates how to use the protocol programmatically.
"""
from poke_protocol_peer import PokeProtocolPeer
from pokemon_loader import PokemonLoader
import time


def example_host():
    """Example of running as a host."""
    print("=== HOST EXAMPLE ===")
    
    # Create host peer
    host = PokeProtocolPeer("HostPlayer", port=8888, is_host=True)
    
    # Set up callbacks
    def on_chat(sender, content_type, content):
        print(f"[CHAT] {sender}: {content}")
    
    def on_battle_update(message):
        print(f"[BATTLE] {message}")
    
    def on_game_over(winner, loser):
        print(f"[GAME OVER] Winner: {winner}, Loser: {loser}")
    
    host.on_chat_received = on_chat
    host.on_battle_update = on_battle_update
    host.on_game_over = on_game_over
    
    # Load Pokemon
    loader = PokemonLoader()
    pikachu = loader.get_pokemon("Pikachu")
    if pikachu:
        host.my_pokemon = pikachu
    
    # Start host
    host.start()
    
    print("Host started. Waiting for joiner...")
    print("In a real scenario, you would interact via the command line.")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        host.stop()
        print("Host stopped.")


def example_joiner():
    """Example of running as a joiner."""
    print("=== JOINER EXAMPLE ===")
    
    # Create joiner peer
    joiner = PokeProtocolPeer("JoinerPlayer", port=8889, is_host=False)
    
    # Set up callbacks
    def on_chat(sender, content_type, content):
        print(f"[CHAT] {sender}: {content}")
    
    def on_battle_update(message):
        print(f"[BATTLE] {message}")
    
    def on_game_over(winner, loser):
        print(f"[GAME OVER] Winner: {winner}, Loser: {loser}")
    
    joiner.on_chat_received = on_chat
    joiner.on_battle_update = on_battle_update
    joiner.on_game_over = on_game_over
    
    # Load Pokemon
    loader = PokemonLoader()
    charmander = loader.get_pokemon("Charmander")
    if charmander:
        joiner.my_pokemon = charmander
    
    # Start joiner
    joiner.start()
    
    # Connect to host
    joiner.connect_as_joiner(("127.0.0.1", 8888))
    
    print("Joiner started. Connected to host.")
    print("In a real scenario, you would interact via the command line.")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        joiner.stop()
        print("Joiner stopped.")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'joiner':
        example_joiner()
    else:
        example_host()

