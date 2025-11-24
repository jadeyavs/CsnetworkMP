"""
Main Application
Command-line interface for PokeProtocol peer.
"""
import sys
import argparse
from poke_protocol_peer import PokeProtocolPeer
from pokemon_loader import PokemonLoader


def main():
    parser = argparse.ArgumentParser(description='PokeProtocol Peer')
    parser.add_argument('--name', type=str, default='Player', help='Player name')
    parser.add_argument('--port', type=int, default=8888, help='UDP port')
    parser.add_argument('--host', action='store_true', help='Run as host')
    parser.add_argument('--connect', type=str, help='Connect to host (IP:PORT)')
    parser.add_argument('--spectator', action='store_true', help='Join as spectator')
    parser.add_argument('--pokemon', type=str, help='Pokemon name to use')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose mode (show all protocol messages)')
    
    args = parser.parse_args()
    
    # Create peer
    peer = PokeProtocolPeer(args.name, args.port, args.host, args.verbose)
    
    # Set up callbacks
    def on_chat(sender, content_type, content):
        if content_type == 'TEXT':
            print(f"[CHAT] {sender}: {content}")
        else:
            print(f"[CHAT] {sender} sent a sticker")
    
    def on_battle_update(message):
        print(f"[BATTLE] {message}")
    
    def on_game_over(winner, loser):
        print(f"[GAME OVER] Winner: {winner}, Loser: {loser}")
    
    peer.on_chat_received = on_chat
    peer.on_battle_update = on_battle_update
    peer.on_game_over = on_game_over
    
    # Start peer
    peer.start()
    
    # Connect if joiner or spectator
    if args.connect:
        host_ip, host_port = args.connect.split(':')
        host_port = int(host_port)
        
        if args.spectator:
            peer.connect_as_spectator((host_ip, host_port))
        else:
            peer.connect_as_joiner((host_ip, host_port))
    
    # Set Pokemon if provided
    if args.pokemon:
        loader = PokemonLoader()
        pokemon = loader.get_pokemon(args.pokemon)
        if pokemon:
            peer.my_pokemon = pokemon
            if peer.connected or peer.is_host:
                peer.send_battle_setup(args.pokemon)
        else:
            print(f"Error: Pokemon '{args.pokemon}' not found")
            print("Available Pokemon (first 20):")
            all_pokemon = loader.list_all_pokemon()[:20]
            for p in all_pokemon:
                print(f"  - {p}")
            sys.exit(1)
    
    # Interactive loop
    try:
        print("\nCommands:")
        print("  attack <move_name> - Attack with a move")
        print("  chat <message> - Send a text chat message")
        print("  pokemon <name> - Set your Pokemon")
        print("  quit - Exit the application")
        if args.verbose:
            print("\n[Verbose mode enabled - all protocol messages will be shown]")
        print()
        
        while True:
            try:
                cmd = input(f"[{args.name}]> ").strip().split()
                if not cmd:
                    continue
                
                if cmd[0] == 'quit':
                    break
                elif cmd[0] == 'attack' and len(cmd) > 1:
                    move_name = ' '.join(cmd[1:])
                    try:
                        peer.send_attack(move_name)
                    except Exception as e:
                        print(f"Error: {e}")
                elif cmd[0] == 'chat' and len(cmd) > 1:
                    message = ' '.join(cmd[1:])
                    peer.send_chat('TEXT', message_text=message)
                elif cmd[0] == 'pokemon' and len(cmd) > 1:
                    pokemon_name = ' '.join(cmd[1:])
                    loader = PokemonLoader()
                    pokemon = loader.get_pokemon(pokemon_name)
                    if pokemon:
                        peer.my_pokemon = pokemon
                        peer.send_battle_setup(pokemon_name)
                        print(f"Set Pokemon to {pokemon_name}")
                    else:
                        print(f"Pokemon '{pokemon_name}' not found")
                else:
                    print("Unknown command")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    finally:
        peer.stop()
        print("\nGoodbye!")


if __name__ == '__main__':
    main()

