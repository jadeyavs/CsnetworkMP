"""
PokeProtocol Peer
Main implementation of a PokeProtocol peer (Host, Joiner, or Spectator).
"""
import socket
import threading
import json
import random
from typing import Optional, Callable, Dict, Tuple
from message_protocol import MessageProtocol
from reliability_layer import ReliabilityLayer
from battle_engine import BattleEngine, BattleState
from pokemon_loader import PokemonLoader, PokemonData


class PokeProtocolPeer:
    """A peer in the PokeProtocol network."""
    
    def __init__(self, name: str, port: int = 8888, is_host: bool = False, verbose: bool = False):
        """
        Initialize a peer.
        
        Args:
            name: Name of this peer
            port: UDP port to listen on
            is_host: True if this peer is the host
            verbose: If True, print all reliability and protocol messages
        """
        self.name = name
        self.port = port
        self.is_host = is_host
        self.is_spectator = False
        self.verbose = verbose
        
        # Network
        self.socket: Optional[socket.socket] = None
        self.remote_address: Optional[Tuple[str, int]] = None
        self.reliability: Optional[ReliabilityLayer] = None
        
        # Battle
        self.battle_engine: Optional[BattleEngine] = None
        self.seed: Optional[int] = None
        self.pokemon_loader = PokemonLoader()
        self.my_pokemon: Optional[PokemonData] = None
        self.opponent_pokemon: Optional[PokemonData] = None
        self.my_stat_boosts: Dict[str, int] = {'special_attack_uses': 5, 'special_defense_uses': 5}
        self.opponent_stat_boosts: Dict[str, int] = {'special_attack_uses': 5, 'special_defense_uses': 5}
        self.communication_mode = "P2P"
        self.received_opponent_setup = False
        self.sent_my_setup = False
        
        # State
        self.connected = False
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_chat_received: Optional[Callable[[str, str, Optional[str]]]] = None
        self.on_battle_update: Optional[Callable[[str]]] = None
        self.on_game_over: Optional[Callable[[str, str]]] = None
    
    def start(self):
        """Start the peer and begin listening."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.port))
        self.socket.settimeout(1.0)  # Timeout for receiving
        
        self.reliability = ReliabilityLayer(self._send_raw)
        self.reliability.start()
        
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        
        if self.is_host:
            print(f"[{self.name}] Listening on port {self.port} as HOST")
        else:
            print(f"[{self.name}] Listening on port {self.port}")
    
    def stop(self):
        """Stop the peer."""
        self.running = False
        if self.reliability:
            self.reliability.stop()
        if self.socket:
            self.socket.close()
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
    
    def connect_as_joiner(self, host_address: Tuple[str, int]):
        """Connect to a host as a joiner."""
        self.remote_address = host_address
        seq = self.reliability.get_next_sequence_number()
        message = MessageProtocol.create_handshake_request(seq)
        self.reliability.send_message(message, seq)
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Sent HANDSHAKE_REQUEST (seq={seq}) to {host_address}")
    
    def connect_as_spectator(self, host_address: Tuple[str, int]):
        """Connect to a host as a spectator."""
        self.is_spectator = True
        self.remote_address = host_address
        seq = self.reliability.get_next_sequence_number()
        message = MessageProtocol.create_spectator_request(seq)
        self.reliability.send_message(message, seq)
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Sent SPECTATOR_REQUEST (seq={seq}) to {host_address}")
    
    def send_battle_setup(self, pokemon_name: str, communication_mode: str = "P2P"):
        """Send battle setup message."""
        if not self.my_pokemon:
            pokemon = self.pokemon_loader.get_pokemon(pokemon_name)
            if not pokemon:
                raise ValueError(f"Pokemon {pokemon_name} not found")
            self.my_pokemon = pokemon
        
        seq = self.reliability.get_next_sequence_number()
        message = MessageProtocol.create_battle_setup(
            communication_mode, self.my_pokemon.name,
            self.my_stat_boosts, self.my_pokemon.to_dict(), seq
        )
        self.reliability.send_message(message, seq)
        self.sent_my_setup = True
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Sent BATTLE_SETUP (seq={seq}) with {pokemon_name}")
    
    def send_attack(self, move_name: str):
        """Send an attack announcement."""
        if not self.battle_engine or not self.battle_engine.can_attack():
            raise ValueError("Cannot attack at this time")
        
        seq = self.battle_engine.announce_attack(move_name)
        message = MessageProtocol.create_attack_announce(move_name, seq)
        self.reliability.send_message(message, seq)
        
        # Calculate and send our calculation report
        calculation = self.battle_engine.calculate_turn(move_name, True)
        self.battle_engine.apply_calculation(calculation, True)
        
        calc_msg = MessageProtocol.create_calculation_report(
            calculation['attacker'], calculation['move_used'],
            calculation['remaining_health'], calculation['damage_dealt'],
            calculation['defender_hp_remaining'], calculation['status_message'],
            seq + 1
        )
        self.reliability.send_message(calc_msg, seq + 1)
        
        if self.on_battle_update:
            self.on_battle_update(calculation['status_message'])
        
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Sent ATTACK_ANNOUNCE (seq={seq}): {move_name}")
            print(f"[{self.name}] [VERBOSE] Sent CALCULATION_REPORT (seq={seq + 1})")
        
        # Check for game over after sending attack
        if self.battle_engine.opponent_current_hp <= 0:
            self._send_game_over()
    
    def send_chat(self, content_type: str, message_text: Optional[str] = None,
                  sticker_data: Optional[str] = None):
        """Send a chat message."""
        seq = self.reliability.get_next_sequence_number()
        message = MessageProtocol.create_chat_message(
            self.name, content_type, message_text, sticker_data, seq
        )
        self.reliability.send_message(message, seq)
    
    def _send_raw(self, data: bytes):
        """Send raw bytes over UDP."""
        if self.remote_address and self.socket:
            self.socket.sendto(data, self.remote_address)
    
    def _receive_loop(self):
        """Main receive loop for incoming messages."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                
                # Set remote address if not set
                if not self.remote_address:
                    self.remote_address = addr
                
                # Parse message
                try:
                    msg = MessageProtocol.parse_message(data)
                    self._handle_message(msg, addr)
                except Exception as e:
                    # Error messages should always be printed
                    print(f"[{self.name}] Error parsing message: {e}")
                    if self.verbose:
                        print(f"[{self.name}] [VERBOSE] Message data: {data[:100]}...")
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    # Error messages should always be printed
                    print(f"[{self.name}] Error in receive loop: {e}")
    
    def _handle_message(self, msg: Dict, addr: Tuple[str, int]):
        """Handle an incoming message."""
        msg_type = msg.get('message_type')
        
        # Handle ACKs
        if msg_type == 'ACK':
            ack_num = int(msg.get('ack_number', 0))
            self.reliability.handle_ack(ack_num)
            if self.verbose:
                print(f"[{self.name}] [VERBOSE] Received ACK (ack={ack_num})")
            return
        
        # Send ACK for non-ACK messages
        if 'sequence_number' in msg:
            seq = int(msg['sequence_number'])
            if not self.reliability.is_duplicate(seq):
                ack = MessageProtocol.create_ack(seq)
                self._send_raw(ack)
                if self.verbose:
                    print(f"[{self.name}] [VERBOSE] Sent ACK (ack={seq}) for message type {msg_type}")
            else:
                if self.verbose:
                    print(f"[{self.name}] [VERBOSE] Duplicate message (seq={seq}), ignoring")
                return  # Duplicate message, ignore
        
        # Handle message types
        if msg_type == 'HANDSHAKE_REQUEST':
            self._handle_handshake_request(msg, addr)
        elif msg_type == 'HANDSHAKE_RESPONSE':
            self._handle_handshake_response(msg)
        elif msg_type == 'SPECTATOR_REQUEST':
            self._handle_spectator_request(msg, addr)
        elif msg_type == 'BATTLE_SETUP':
            self._handle_battle_setup(msg)
        elif msg_type == 'ATTACK_ANNOUNCE':
            self._handle_attack_announce(msg)
        elif msg_type == 'DEFENSE_ANNOUNCE':
            self._handle_defense_announce(msg)
        elif msg_type == 'CALCULATION_REPORT':
            self._handle_calculation_report(msg)
        elif msg_type == 'CALCULATION_CONFIRM':
            self._handle_calculation_confirm(msg)
        elif msg_type == 'RESOLUTION_REQUEST':
            self._handle_resolution_request(msg)
        elif msg_type == 'GAME_OVER':
            self._handle_game_over(msg)
        elif msg_type == 'CHAT_MESSAGE':
            self._handle_chat_message(msg)
    
    def _handle_handshake_request(self, msg: Dict, addr: Tuple[str, int]):
        """Handle handshake request (host only)."""
        if not self.is_host:
            return
        
        self.remote_address = addr
        self.seed = random.randint(1, 1000000)
        seq = self.reliability.get_next_sequence_number()
        response = MessageProtocol.create_handshake_response(self.seed, seq)
        self.reliability.send_message(response, seq)
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Received HANDSHAKE_REQUEST, sent HANDSHAKE_RESPONSE (seq={seq}) with seed {self.seed}")
        
        # Initialize battle engine with seed
        if not self.battle_engine and self.seed and not self.is_spectator:
            self.battle_engine = BattleEngine(self.seed, self.is_host)
        
        # Send battle setup if we have a Pokemon
        if self.my_pokemon:
            self.send_battle_setup(self.my_pokemon.name)
    
    def _handle_handshake_response(self, msg: Dict):
        """Handle handshake response (joiner only)."""
        if self.is_host:
            return
        
        self.seed = int(msg.get('seed', 0))
        self.connected = True
        if self.verbose:
            seq = msg.get('sequence_number', '?')
            print(f"[{self.name}] [VERBOSE] Received HANDSHAKE_RESPONSE (seq={seq}) with seed {self.seed}")
        
        # Send battle setup if we have a Pokemon
        if self.my_pokemon:
            self.send_battle_setup(self.my_pokemon.name)
    
    def _handle_spectator_request(self, msg: Dict, addr: Tuple[str, int]):
        """Handle spectator request (host only)."""
        if not self.is_host:
            return
        
        self.remote_address = addr
        # Spectators don't need a seed, but we can send one for consistency
        if not self.seed:
            self.seed = random.randint(1, 1000000)
        seq = self.reliability.get_next_sequence_number()
        response = MessageProtocol.create_handshake_response(self.seed, seq)
        self.reliability.send_message(response, seq)
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Received SPECTATOR_REQUEST, sent HANDSHAKE_RESPONSE (seq={seq})")
    
    def _handle_battle_setup(self, msg: Dict):
        """Handle battle setup message."""
        pokemon_data = json.loads(msg.get('pokemon', '{}'))
        opponent_name = msg.get('pokemon_name', '')
        comm_mode = msg.get('communication_mode', 'P2P')
        stat_boosts = json.loads(msg.get('stat_boosts', '{}'))
        
        # Load opponent Pokemon
        self.opponent_pokemon = self.pokemon_loader.get_pokemon(opponent_name)
        if not self.opponent_pokemon:
            # Error messages should always be printed
            print(f"[{self.name}] Error: Could not load opponent Pokemon {opponent_name}")
            return
        
        self.opponent_stat_boosts = stat_boosts
        self.communication_mode = comm_mode
        
        if self.verbose:
            seq = msg.get('sequence_number', '?')
            print(f"[{self.name}] [VERBOSE] Received BATTLE_SETUP (seq={seq}): Opponent is {opponent_name}")
        else:
            print(f"[{self.name}] Opponent is {opponent_name}")
        self.received_opponent_setup = True
        
        # Initialize battle engine if we have both Pokemon, seed, and both setups are done
        if self.seed and not self.is_spectator and self.my_pokemon and self.opponent_pokemon:
            if not self.battle_engine:
                self.battle_engine = BattleEngine(self.seed, self.is_host)
            
            # Setup battle if not already done
            if self.battle_engine.state == BattleState.SETUP:
                self.battle_engine.setup_battle(
                    self.my_pokemon, self.opponent_pokemon,
                    self.my_stat_boosts, self.opponent_stat_boosts
                )
                print(f"[{self.name}] Battle initialized! {'You go first' if self.is_host else 'Opponent goes first'}")
    
    def _handle_attack_announce(self, msg: Dict):
        """Handle attack announce message."""
        if self.is_spectator:
            if self.on_battle_update:
                self.on_battle_update(f"Opponent used {msg.get('move_name')}!")
            return
        
        if not self.battle_engine:
            return
        
        move_name = msg.get('move_name', '')
        seq = self.battle_engine.receive_attack_announce(move_name)
        
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Received ATTACK_ANNOUNCE (seq={seq}): {move_name}")
        
        # Send defense announce
        defense_msg = MessageProtocol.create_defense_announce(seq)
        self.reliability.send_message(defense_msg, seq)
        
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Sent DEFENSE_ANNOUNCE (seq={seq})")
        
        # Calculate damage
        calculation = self.battle_engine.calculate_turn(move_name, False)
        self.battle_engine.apply_calculation(calculation, False)
        
        # Send calculation report
        calc_seq = seq + 1
        calc_msg = MessageProtocol.create_calculation_report(
            calculation['attacker'], calculation['move_used'],
            calculation['remaining_health'], calculation['damage_dealt'],
            calculation['defender_hp_remaining'], calculation['status_message'],
            calc_seq
        )
        self.reliability.send_message(calc_msg, calc_seq)
        
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Sent CALCULATION_REPORT (seq={calc_seq})")
        
        if self.on_battle_update:
            self.on_battle_update(calculation['status_message'])
        
        # Check for game over after receiving attack
        if self.battle_engine.my_current_hp <= 0:
            self._send_game_over()
    
    def _handle_defense_announce(self, msg: Dict):
        """Handle defense announce message."""
        if self.is_spectator or not self.battle_engine:
            return
        
        # Defense announce confirms the opponent received our attack
        # Our calculation report should already be sent in send_attack
        # This just confirms they're ready to process
        pass
    
    def _handle_calculation_report(self, msg: Dict):
        """Handle calculation report message."""
        if self.is_spectator:
            if self.on_battle_update:
                self.on_battle_update(msg.get('status_message', ''))
            return
        
        if not self.battle_engine:
            return
        
        calculation = {
            'attacker': msg.get('attacker', ''),
            'move_used': msg.get('move_used', ''),
            'remaining_health': int(msg.get('remaining_health', 0)),
            'damage_dealt': int(msg.get('damage_dealt', 0)),
            'defender_hp_remaining': int(msg.get('defender_hp_remaining', 0)),
            'status_message': msg.get('status_message', '')
        }
        
        if self.verbose:
            seq = msg.get('sequence_number', '?')
            print(f"[{self.name}] [VERBOSE] Received CALCULATION_REPORT (seq={seq})")
        
        # Determine if this is opponent's calculation
        is_opponent = calculation['attacker'] == self.opponent_pokemon_name
        self.battle_engine.apply_calculation(calculation, not is_opponent)
        
        # Check if calculations match
        if self.battle_engine.check_calculations_match():
            seq = int(msg.get('sequence_number', 0)) + 1
            confirm_msg = MessageProtocol.create_calculation_confirm(seq)
            self.reliability.send_message(confirm_msg, seq)
            if self.verbose:
                print(f"[{self.name}] [VERBOSE] Sent CALCULATION_CONFIRM (seq={seq})")
            self.battle_engine.confirm_calculation()
            
            # Check for game over after confirming calculation
            if self.battle_engine.state == BattleState.GAME_OVER:
                self._send_game_over()
        else:
            # Send resolution request
            seq = int(msg.get('sequence_number', 0)) + 1
            my_calc = self.battle_engine.my_calculation
            if my_calc:
                if self.verbose:
                    print(f"[{self.name}] [VERBOSE] Calculation mismatch! Sending RESOLUTION_REQUEST (seq={seq})")
                resolution_msg = MessageProtocol.create_resolution_request(
                    my_calc['attacker'], my_calc['move_used'],
                    my_calc['damage_dealt'], my_calc['defender_hp_remaining'],
                    seq
                )
                self.reliability.send_message(resolution_msg, seq)
    
    def _handle_calculation_confirm(self, msg: Dict):
        """Handle calculation confirm message."""
        if self.is_spectator or not self.battle_engine:
            return
        
        if self.verbose:
            seq = msg.get('sequence_number', '?')
            print(f"[{self.name}] [VERBOSE] Received CALCULATION_CONFIRM (seq={seq})")
        
        self.battle_engine.confirm_calculation()
        
        # Check for game over after confirming
        if self.battle_engine.state == BattleState.GAME_OVER:
            self._send_game_over()
    
    def _handle_resolution_request(self, msg: Dict):
        """Handle resolution request message."""
        if self.is_spectator or not self.battle_engine:
            return
        
        if self.verbose:
            seq = msg.get('sequence_number', '?')
            print(f"[{self.name}] [VERBOSE] Received RESOLUTION_REQUEST (seq={seq})")
        
        # Re-evaluate and accept opponent's calculation if reasonable
        calculation = {
            'attacker': msg.get('attacker', ''),
            'move_used': msg.get('move_used', ''),
            'damage_dealt': int(msg.get('damage_dealt', 0)),
            'defender_hp_remaining': int(msg.get('defender_hp_remaining', 0))
        }
        # Accept and apply
        self.battle_engine.apply_calculation(calculation, False)
        self.battle_engine.confirm_calculation()
        
        # Check for game over
        if self.battle_engine.state == BattleState.GAME_OVER:
            self._send_game_over()
    
    def _handle_game_over(self, msg: Dict):
        """Handle game over message."""
        winner = msg.get('winner', '')
        loser = msg.get('loser', '')
        
        if self.verbose:
            seq = msg.get('sequence_number', '?')
            print(f"[{self.name}] [VERBOSE] Received GAME_OVER (seq={seq})")
        
        if self.on_game_over:
            self.on_game_over(winner, loser)
        
        print(f"[{self.name}] GAME OVER - Winner: {winner}, Loser: {loser}")
    
    def _handle_chat_message(self, msg: Dict):
        """Handle chat message."""
        sender = msg.get('sender_name', '')
        content_type = msg.get('content_type', 'TEXT')
        message_text = msg.get('message_text', '')
        sticker_data = msg.get('sticker_data', '')
        
        if content_type == 'STICKER' and sticker_data:
            # Save sticker to file
            import base64
            import os
            from datetime import datetime
            
            try:
                # Decode Base64
                image_data = base64.b64decode(sticker_data)
                
                # Create stickers directory if it doesn't exist
                os.makedirs('stickers', exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"stickers/sticker_{sender}_{timestamp}.png"
                
                # Save to file
                with open(filename, 'wb') as f:
                    f.write(image_data)
                
                if self.verbose:
                    print(f"[{self.name}] [VERBOSE] Saved sticker from {sender} to {filename}")
            except Exception as e:
                if self.verbose:
                    print(f"[{self.name}] [VERBOSE] Error saving sticker: {e}")
        
        if self.on_chat_received:
            self.on_chat_received(sender, content_type, 
                                 message_text if content_type == 'TEXT' else sticker_data)
    
    def _send_game_over(self):
        """Send GAME_OVER message when a Pokemon faints."""
        if not self.battle_engine:
            return
        
        winner = self.battle_engine.get_winner()
        if winner:
            if winner == self.my_pokemon_name:
                loser = self.opponent_pokemon_name
            else:
                loser = self.my_pokemon_name
            
            seq = self.reliability.get_next_sequence_number()
            game_over_msg = MessageProtocol.create_game_over(winner, loser, seq)
            self.reliability.send_message(game_over_msg, seq)
            
            if self.verbose:
                print(f"[{self.name}] [VERBOSE] Sent GAME_OVER (seq={seq}): Winner={winner}, Loser={loser}")

