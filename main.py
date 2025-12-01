"""
Main Application
Command-line interface for PokeProtocol peer.
"""
import sys
import argparse
import time
from poke_protocol_peer import PokeProtocolPeer
from pokemon_loader import PokemonLoader
from pokemon_selector import PokemonSelector


def get_connection_choice(args, default_port):
    """
    Get connection choice from user or command line arguments.
    Returns: (is_host, connect_address, joiner_port, is_spectator) 
    where connect_address is (ip, port) or None, and joiner_port is the port for joiner
    """     # If command line arguments specify, use those
    if args.spectator:
        if args.connect:
            host_ip, host_port = args.connect.split(':')
            return (False, (host_ip, int(host_port)), default_port, True)  # (is_host, connect_address, joiner_port, is_spectator)
        else:
            print("Error: Spectator mode requires --connect option")
            sys.exit(1)
    
    if args.host:
        return (True, None, default_port, False)  # Host mode
    
    if args.connect:
        host_ip, host_port = args.connect.split(':')
        host_port = int(host_port)
        # Ensure joiner port is different from host port
        joiner_port = default_port
        if joiner_port == host_port:
            joiner_port = host_port + 1
        return (False, (host_ip, host_port), joiner_port, False)  # Joiner mode
    
    # Interactive choice
    print("\n" + "=" * 60)
    print("CONNECTION MODE")
    print("=" * 60)
    print("1. Host a battle (wait for another player to join)")
    print("2. Join a battle (connect to a host)")
    print("=" * 60)
    
    while True:
        try:
            choice = input("\nEnter your choice (1 or 2): ").strip()
            
            if choice == '1':
                return (True, None, default_port, False)  # Host mode
            elif choice == '2':
                # Ask for joiner's port first
                while True:
                    try:
                        port_input = input(f"Enter your port number (default: {default_port + 1}): ").strip()
                        if not port_input:
                            joiner_port = default_port + 1
                        else:
                            joiner_port = int(port_input)
                        
                        if joiner_port < 1024 or joiner_port > 65535:
                            print("Port must be between 1024 and 65535")
                            continue
                        break
                    except ValueError:
                        print("Invalid port number. Please enter a number.")
                
                # Ask for host address
                while True:
                    address_input = input("Enter host address (IP:PORT, e.g., 127.0.0.1:8888): ").strip()
                    try:
                        if ':' in address_input:
                            host_ip, host_port = address_input.split(':')
                            host_port = int(host_port)
                            
                            # Ensure joiner port is different from host port
                            if joiner_port == host_port:
                                print(f"Warning: Your port ({joiner_port}) cannot be the same as the host port ({host_port})")
                                print(f"Automatically changing your port to {host_port + 1}")
                                joiner_port = host_port + 1
                            
                            return (False, (host_ip, host_port), joiner_port, False)  # Joiner mode
                        else:
                            print("Invalid format. Please use IP:PORT (e.g., 127.0.0.1:8888)")
                    except ValueError:
                        print("Invalid port number. Please use IP:PORT (e.g., 127.0.0.1:8888)")
            else:
                print("Invalid choice. Please enter 1 or 2.")
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='PokeProtocol Peer')
    parser.add_argument('--name', type=str, default='Player', help='Player name')
    parser.add_argument('--port', type=int, default=8888, help='UDP port')
    parser.add_argument('--host', action='store_true', help='Run as host')
    parser.add_argument('--connect', type=str, help='Connect to host (IP:PORT)')
    parser.add_argument('--spectator', action='store_true', help='Join as spectator')
    parser.add_argument('--pokemon', type=str, help='Pokemon name to use (skips selection)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose mode (show all protocol messages)')
    
    args = parser.parse_args()
    
    # Load Pokemon data
    loader = PokemonLoader()
    
    # Main application loop (allows for returning to menu)
    first_run = True
    while True:
        # Select Pokemon if not provided via command line
        selected_pokemon = None
        if args.pokemon and first_run:
            selected_pokemon = loader.get_pokemon(args.pokemon)
            if not selected_pokemon:
                print(f"Error: Pokemon '{args.pokemon}' not found")
                sys.exit(1)
        else:
            # Interactive Pokemon selection
            if not args.spectator:
                selector = PokemonSelector(loader)
                selected_pokemon = selector.select_pokemon()
                if not selected_pokemon:
                    print("No Pokemon selected. Exiting...")
                    sys.exit(0)
        
        # Get connection choice (host or join) - do this before creating peer
        is_host, connect_address, joiner_port, is_spectator = get_connection_choice(args, args.port)
        
        # Determine which port to use
        if is_host:
            peer_port = args.port
        else:
            peer_port = joiner_port
        
        # Adjust name based on role
        player_name = args.name
        if player_name == 'Player':
            if is_host:
                player_name = "Player 1 [HOST]"
            elif not is_spectator:
                player_name = "Player 2"
        else:
            # Only append [HOST] if not already there (in case of re-run)
            if is_host and "[HOST]" not in player_name:
                player_name = f"{player_name} [HOST]"
    
        # Create peer with correct role and port
        peer = PokeProtocolPeer(player_name, peer_port, is_host, args.verbose)
        
        # Set up callbacks
        def on_chat(sender, content_type, content):
            # ANSI color codes
            BLUE = '\033[94m'
            RED = '\033[91m'
            RESET = '\033[0m'
            
            if content_type == 'TEXT':
                # Color own messages blue, opponent messages red
                if sender == player_name:
                    print(f"{BLUE}{sender}: {content}{RESET}")
                else:
                    print(f"{RED}{sender}: {content}{RESET}")
            else:
                if sender == player_name:
                    print(f"{BLUE}{sender} sent a sticker{RESET}")
                else:
                    print(f"{RED}{sender} sent a sticker{RESET}")
        
        def on_battle_update(message):
            print(f"[BATTLE] {message}")
        
        def on_game_over(winner, loser):
            print(f"[GAME OVER] Winner: {winner}, Loser: {loser}")
        
        peer.on_chat_received = on_chat
        peer.on_battle_update = on_battle_update
        peer.on_game_over = on_game_over
        
        # Set Pokemon
        peer.my_pokemon = selected_pokemon
        
        # Game Loop
        quit_to_menu = False
        
        # Start peer
        peer.start()
        
        # Startup flow based on role
        if is_spectator:
            # Spectator: Connect to host
            peer.is_spectator = True
            peer.connect_as_spectator(connect_address)
            print(f"[{player_name}] Connecting as spectator to {connect_address[0]}:{connect_address[1]}...")
        
        elif is_host:
            # Host: Wait for joiner to connect
            print(f"\n[{player_name}] Waiting for joiner to connect...")
            if selected_pokemon:
                print(f"[{player_name}] Selected Pokemon: {selected_pokemon.name}")
            print(f"[{player_name}] Listening on port {args.port}")
            print(f"[{player_name}] Share this address with the other player: <your-ip>:{args.port}")
            
            # Wait for handshake request from joiner
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            while not peer.remote_address and (time.time() - start_time) < max_wait_time:
                time.sleep(0.1)
            
            if not peer.remote_address:
                print(f"[{player_name}] No joiner connected within {max_wait_time} seconds. Exiting...")
                peer.stop()
                sys.exit(1)
            
            print(f"[{player_name}] Joiner connected! Handshake completed.")
            
            # Send battle setup after handshake
            if peer.my_pokemon and not peer.sent_my_setup:
                peer.send_battle_setup(peer.my_pokemon.name)
        
        else:
            # Joiner: Look for host and connect
            host_ip, host_port = connect_address
            print(f"\n[{player_name}] Looking for host at {host_ip}:{host_port}...")
            if selected_pokemon:
                print(f"[{player_name}] Selected Pokemon: {selected_pokemon.name}")
            print(f"[{player_name}] Listening on port {peer_port}")
            
            peer.connect_as_joiner((host_ip, host_port))
            
            # Wait for handshake response
            max_wait_time = 30
            start_time = time.time()
            while not peer.connected and (time.time() - start_time) < max_wait_time:
                time.sleep(0.1)
            
            if not peer.connected:
                print(f"[{player_name}] Failed to connect to host. Exiting...")
                peer.stop()
                sys.exit(1)
            
            print(f"[{player_name}] Connected to host! Handshake completed.")
            
            # Send battle setup after handshake
            if peer.my_pokemon and not peer.sent_my_setup:
                peer.send_battle_setup(peer.my_pokemon.name)
        
        # Interactive loop
        game_over = False
        
        def on_game_over_callback(winner, loser):
            nonlocal game_over
            game_over = True
        
        peer.on_game_over = on_game_over_callback
        
        try:
            print("\nCommands:")
            print("  attack <move_name> - Attack with a move")
            print("  chat <message> - Send a text chat message")
            print("  pokemon <name> - Set your Pokemon")
            print("  quit - Exit the application")
            if args.verbose:
                print("\n[Verbose mode enabled - all protocol messages will be shown]")
            print()
            
            while not game_over:
                try:
                    cmd = input(f"[{player_name}]> ").strip().split()
                    if not cmd:
                        continue
                    
                    if cmd[0] == 'quit':
                        peer.stop()
                        print("\nGoodbye!")
                        sys.exit(0)
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
            
            # Game Over - return to menu
            if game_over:
                print("\n" + "=" * 60)
                print("GAME OVER")
                print("=" * 60)
                print("Returning to main menu...")
                print("=" * 60)
                time.sleep(2)  # Brief pause before returning to menu
                
                # Stop peer - a new one will be created in the next loop iteration
                peer.stop()
                quit_to_menu = True
        
        except KeyboardInterrupt:
            peer.stop()
            print("\nGoodbye!")
            sys.exit(0)
        
        # End of Game Loop
        first_run = False
        if not quit_to_menu:
            # If we broke out without quit_to_menu (e.g. KeyboardInterrupt), exit app
            peer.stop()
            print("\nGoodbye!")
            break


if __name__ == '__main__':
    main()

