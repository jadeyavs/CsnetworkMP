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
    
    def _hp_bar(self, current: int, maximum: int, name: str, is_mine: bool = False) -> str:
        """Create an HP bar string with color coding."""
        # ANSI color codes
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        RESET = '\033[0m'
        
        percentage = (current / maximum * 100) if maximum > 0 else 0
        bar_length = 30
        filled = int(bar_length * current / maximum) if maximum > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        prefix = "YOU: " if is_mine else "OPPONENT: "
        
        # Choose color based on HP percentage
        if percentage >= 65:
            color = GREEN
        elif percentage >= 25:
            color = YELLOW
        else:
            color = RED
        
        return f"{prefix}{name:15s} [{color}{bar}{RESET}] {current:3d}/{maximum:3d} ({percentage:5.1f}%)"
    
    def _display_initial_battle_stats(self):
        """Display initial battle statistics when battle starts."""
        if not self.battle_engine:
            return
        
        my_hp = self.battle_engine.my_current_hp
        my_max_hp = self.battle_engine.my_pokemon.hp
        opp_hp = self.battle_engine.opponent_current_hp
        opp_max_hp = self.battle_engine.opponent_pokemon.hp
        
        print("\n" + "=" * 60)
        print("BATTLE STARTED!")
        print("=" * 60)
        print(self._hp_bar(my_hp, my_max_hp, self.battle_engine.my_pokemon_name, True))
        print(self._hp_bar(opp_hp, opp_max_hp, self.battle_engine.opponent_pokemon_name, False))
        print("=" * 60 + "\n")
    
    def _display_battle_stats(self, calculation: Dict):
        """Display battle statistics after an attack with detailed calculations."""
        if not self.battle_engine:
            return
        
        attacker_name = calculation['attacker']
        move_name = calculation['move_used']
        damage = calculation['damage_dealt']
        status_msg = calculation.get('status_message', '')
        
        # Get move information for detailed display
        from damage_calculator import get_move_info
        move_info = get_move_info(move_name)
        move_type = move_info.get('type', 'normal').capitalize()
        move_category = move_info.get('category', 'physical').capitalize()
        move_power = move_info.get('power', 40.0)
        
        # Get current HP values (should be updated after apply_calculation)
        my_hp = self.battle_engine.my_current_hp
        my_max_hp = self.battle_engine.my_pokemon.hp
        opp_hp = self.battle_engine.opponent_current_hp
        opp_max_hp = self.battle_engine.opponent_pokemon.hp
        
        # Calculate previous HP (before damage was applied)
        # If I attacked, opponent took damage, so opponent's previous HP = current + damage
        # If opponent attacked, I took damage, so my previous HP = current + damage
        if attacker_name == self.battle_engine.my_pokemon_name:
            # I attacked, opponent took damage
            defender_name = self.battle_engine.opponent_pokemon_name
            defender_prev_hp = min(opp_hp + damage, opp_max_hp)  # Previous HP before damage
            defender_curr_hp = opp_hp  # Current HP after damage
            defender_max_hp = opp_max_hp
        else:
            # Opponent attacked, I took damage
            defender_name = self.battle_engine.my_pokemon_name
            defender_prev_hp = min(my_hp + damage, my_max_hp)  # Previous HP before damage
            defender_curr_hp = my_hp  # Current HP after damage
            defender_max_hp = my_max_hp
        
        # Display battle statistics
        print("\n" + "=" * 70)
        print("BATTLE REPORT")
        print("=" * 70)
        print(f"⚔️  {attacker_name} used {move_name}!")
        print(f"   Type: {move_type} | Category: {move_category} | Power: {move_power}")
        print("-" * 70)
        print("CALCULATION:")
        print(f"   Damage dealt: {damage} HP")
        print(f"   {defender_name}: {defender_prev_hp} HP → {defender_curr_hp} HP")
        if status_msg and status_msg != f"{attacker_name} used {move_name}!":
            print(f"   {status_msg.split('!')[1] if '!' in status_msg else status_msg}")
        print("-" * 70)
        
        # Check if a Pokemon fainted
        fainted_pokemon = None
        if my_hp <= 0:
            fainted_pokemon = self.battle_engine.my_pokemon_name
        elif opp_hp <= 0:
            fainted_pokemon = self.battle_engine.opponent_pokemon_name
        
        if fainted_pokemon:
            print(f"💀 {fainted_pokemon} has been taken down!")
            print("-" * 70)
        
        print("CURRENT STATUS:")
        print(self._hp_bar(my_hp, my_max_hp, self.battle_engine.my_pokemon_name, True))
        print(self._hp_bar(opp_hp, opp_max_hp, self.battle_engine.opponent_pokemon_name, False))
        print("=" * 70 + "\n")
    
    def send_attack(self, move_name: str):
        """Send an attack announcement."""
        if not self.battle_engine or not self.battle_engine.can_attack():
            raise ValueError("Cannot attack at this time")
        
        # Verify we have a remote address to send to
        if not self.remote_address:
            raise ValueError("Cannot attack: Not connected to opponent. Remote address not set.")
        
        seq = self.battle_engine.announce_attack(move_name)
        message = MessageProtocol.create_attack_announce(move_name, seq)
        self.reliability.send_message(message, seq)
        
        print(f"[{self.name}] Attacking with {move_name}...")
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Sent ATTACK_ANNOUNCE (seq={seq}): {move_name} to {self.remote_address}")
        
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
        
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Sent CALCULATION_REPORT (seq={seq + 1}) to {self.remote_address}")
        
        # Don't display stats yet - wait for opponent's calculation report to confirm
        # Stats will be displayed when we receive and confirm the opponent's calculation
    
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
        if not self.remote_address:
            if self.verbose:
                print(f"[{self.name}] [VERBOSE] Warning: Attempted to send message but remote_address is not set")
            return
        
        if not self.socket:
            if self.verbose:
                print(f"[{self.name}] [VERBOSE] Warning: Attempted to send message but socket is not set")
            return
        
        try:
            self.socket.sendto(data, self.remote_address)
            if self.verbose:
                print(f"[{self.name}] [VERBOSE] Sent {len(data)} bytes to {self.remote_address}")
        except Exception as e:
            print(f"[{self.name}] Error sending message to {self.remote_address}: {e}")
    
    def _receive_loop(self):
        """Main receive loop for incoming messages."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                
                # Set remote address if not set (for initial connection)
                # But don't override if already set (to maintain connection)
                if not self.remote_address:
                    self.remote_address = addr
                    if self.verbose:
                        print(f"[{self.name}] [VERBOSE] Set remote_address to {addr}")
                elif self.remote_address != addr:
                    # If we receive from a different address, update it (might be NAT issue)
                    if self.verbose:
                        print(f"[{self.name}] [VERBOSE] Received message from different address: {addr} (was {self.remote_address})")
                    self.remote_address = addr
                
                # Parse message
                try:
                    msg = MessageProtocol.parse_message(data)
                    if self.verbose:
                        msg_type = msg.get('message_type', 'UNKNOWN')
                        print(f"[{self.name}] [VERBOSE] Received {msg_type} from {addr}")
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
        
        # Send ACK for non-ACK messages (before processing to avoid duplicate processing)
        if 'sequence_number' in msg:
            seq = int(msg['sequence_number'])
            is_dup = self.reliability.is_duplicate(seq)
            
            # Always send ACK (even for duplicates, in case first ACK was lost)
            ack = MessageProtocol.create_ack(seq)
            self._send_raw(ack)
            
            if is_dup:
                if self.verbose:
                    print(f"[{self.name}] [VERBOSE] Duplicate message (seq={seq}, type={msg_type}), ignoring")
                return  # Duplicate message, ignore (but ACK was sent)
            else:
                if self.verbose:
                    print(f"[{self.name}] [VERBOSE] New message (seq={seq}, type={msg_type}), sent ACK")
        
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
        
        # Set remote address to the joiner's address
        self.remote_address = addr
        print(f"[{self.name}] Received handshake from joiner at {addr}")
        
        self.seed = random.randint(1, 1000000)
        seq = self.reliability.get_next_sequence_number()
        response = MessageProtocol.create_handshake_response(self.seed, seq)
        self.reliability.send_message(response, seq)
        print(f"[{self.name}] Sent handshake response with seed {self.seed} to {addr}")
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Received HANDSHAKE_REQUEST, sent HANDSHAKE_RESPONSE (seq={seq}) with seed {self.seed} to {addr}")
            print(f"[{self.name}] [VERBOSE] Remote address set to: {self.remote_address}")
        
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
        print(f"[{self.name}] Handshake successful! Connected to host. Seed: {self.seed}")
        if self.verbose:
            seq = msg.get('sequence_number', '?')
            print(f"[{self.name}] [VERBOSE] Received HANDSHAKE_RESPONSE (seq={seq}) with seed {self.seed}")
            print(f"[{self.name}] [VERBOSE] Remote address: {self.remote_address}")
        
        # Initialize battle engine with seed
        if not self.battle_engine and self.seed and not self.is_spectator:
            self.battle_engine = BattleEngine(self.seed, self.is_host)
        
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
                # Clear received sequences to avoid conflicts with handshake sequence numbers
                self.reliability.clear_received_sequences()
                if self.verbose:
                    print(f"[{self.name}] [VERBOSE] Cleared received sequences for battle")
                
                self.battle_engine.setup_battle(
                    self.my_pokemon, self.opponent_pokemon,
                    self.my_stat_boosts, self.opponent_stat_boosts
                )
                print(f"[{self.name}] Battle initialized! {'You go first' if self.is_host else 'Opponent goes first'}")
                # Display initial battle statistics
                self._display_initial_battle_stats()
    
    def _handle_attack_announce(self, msg: Dict):
        """Handle attack announce message."""
        if self.is_spectator:
            if self.on_battle_update:
                self.on_battle_update(f"Opponent used {msg.get('move_name')}!")
            return
        
        if not self.battle_engine:
            return
        
        move_name = msg.get('move_name', '')
        print(f"[{self.name}] Opponent is attacking with {move_name}...")
        seq_num = int(msg.get('sequence_number', 0))
        seq = self.battle_engine.receive_attack_announce(move_name, seq_num)
        
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Received ATTACK_ANNOUNCE (seq={seq}): {move_name}")
        
        # Verify we have a remote address to send to
        if not self.remote_address:
            print(f"[{self.name}] Error: Cannot respond to attack - remote address not set")
            return
        
        # Send defense announce
        defense_msg = MessageProtocol.create_defense_announce(seq)
        self.reliability.send_message(defense_msg, seq)
        
        if self.verbose:
            print(f"[{self.name}] [VERBOSE] Sent DEFENSE_ANNOUNCE (seq={seq}) to {self.remote_address}")
        
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
            print(f"[{self.name}] [VERBOSE] Sent CALCULATION_REPORT (seq={calc_seq}) to {self.remote_address}")
        
        # Don't display stats yet - wait for confirmation
        # Stats will be displayed when calculations are confirmed
    
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
        
        # Determine if this is my calculation or opponent's calculation
        # If the attacker is my Pokemon, this is my calculation
        # If the attacker is opponent's Pokemon, this is opponent's calculation
        is_my_calculation = calculation['attacker'] == self.battle_engine.my_pokemon_name
        self.battle_engine.apply_calculation(calculation, is_my_calculation)
        
        # Check if calculations match
        if self.battle_engine.check_calculations_match():
            seq = int(msg.get('sequence_number', 0)) + 1
            confirm_msg = MessageProtocol.create_calculation_confirm(seq)
            self.reliability.send_message(confirm_msg, seq)
            if self.verbose:
                print(f"[{self.name}] [VERBOSE] Sent CALCULATION_CONFIRM (seq={seq})")
            
            # Display battle statistics now that calculations are confirmed
            # Use the confirmed calculation (either mine or opponent's, they should match)
            confirmed_calc = self.battle_engine.my_calculation if self.battle_engine.my_calculation else calculation
            self._display_battle_stats(confirmed_calc)
            
            if self.on_battle_update:
                status_msg = confirmed_calc.get('status_message', '')
                if status_msg:
                    self.on_battle_update(status_msg)
            
            # Confirm and switch turns
            self.battle_engine.confirm_calculation()
            
            # Display turn completion message
            if self.battle_engine.state != BattleState.GAME_OVER:
                print(f"[{self.name}] Turn complete. {'Your turn!' if self.battle_engine.is_my_turn else 'Waiting for opponent...'}")
            
            # Check for game over after confirming calculation
            if self.battle_engine.state == BattleState.GAME_OVER:
                self._send_game_over()
        else:
            # Send resolution request - calculations don't match
            seq = int(msg.get('sequence_number', 0)) + 1
            my_calc = self.battle_engine.my_calculation
            opp_calc = self.battle_engine.opponent_calculation
            
            if self.verbose and my_calc and opp_calc:
                print(f"[{self.name}] [VERBOSE] Calculation mismatch detected!")
                print(f"[{self.name}] [VERBOSE] My calc: attacker={my_calc['attacker']}, move={my_calc['move_used']}, damage={my_calc['damage_dealt']}, defender_hp={my_calc['defender_hp_remaining']}")
                print(f"[{self.name}] [VERBOSE] Opp calc: attacker={opp_calc['attacker']}, move={opp_calc['move_used']}, damage={opp_calc['damage_dealt']}, defender_hp={opp_calc['defender_hp_remaining']}")
            
            if my_calc:
                print(f"[{self.name}] Calculation mismatch! Requesting resolution.")
                if self.verbose:
                    print(f"[{self.name}] [VERBOSE] Sending RESOLUTION_REQUEST (seq={seq})")
                    if opp_calc:
                        print(f"[{self.name}] [VERBOSE] Using opponent's values: damage={opp_calc['damage_dealt']}, defender_hp={opp_calc['defender_hp_remaining']}")
                # Use opponent's calculation values for resolution (they sent it, so we accept theirs)
                if opp_calc:
                    resolution_msg = MessageProtocol.create_resolution_request(
                        opp_calc['attacker'],
                        opp_calc['move_used'],
                        opp_calc['damage_dealt'],
                        opp_calc['defender_hp_remaining'],
                        seq
                    )
                else:
                    # Fallback to our calculation if opponent's isn't available
                    resolution_msg = MessageProtocol.create_resolution_request(
                        my_calc['attacker'],
                        my_calc['move_used'],
                        my_calc['damage_dealt'],
                        my_calc['defender_hp_remaining'],
                        seq
                    )
                self.reliability.send_message(resolution_msg, seq)
                
                # We are accepting opponent's calculation, so we should apply it locally too
                # and display the results, just like the receiver of the resolution request will
                
                # Create calculation dict from the values we're accepting
                accepted_calc = opp_calc if opp_calc else my_calc
                
                # Apply it locally (force it)
                # If we used opp_calc, we need to apply it as opponent's attack or my attack depending on who attacked
                # The 'attacker' field tells us who attacked
                is_opponent_attack = accepted_calc['attacker'] == self.battle_engine.opponent_pokemon_name
                
                # Apply and set both calculations to match
                self.battle_engine.apply_calculation(accepted_calc, not is_opponent_attack)
                if is_opponent_attack:
                    self.battle_engine.my_calculation = accepted_calc.copy()
                else:
                    self.battle_engine.opponent_calculation = accepted_calc.copy()
                
                # Display battle statistics
                self._display_battle_stats(accepted_calc)
                
                if self.on_battle_update:
                    status_msg = accepted_calc.get('status_message', '')
                    if status_msg:
                        self.on_battle_update(status_msg)
                
                # Confirm and switch turns
                if self.battle_engine.confirm_calculation():
                    # Display turn completion message
                    if self.battle_engine.state != BattleState.GAME_OVER:
                        print(f"[{self.name}] Turn complete. {'Your turn!' if self.battle_engine.is_my_turn else 'Waiting for opponent...'}")
                    
                    # Check for game over
                    if self.battle_engine.state == BattleState.GAME_OVER:
                        self._send_game_over()
    
    def _handle_calculation_confirm(self, msg: Dict):
        """Handle calculation confirm message."""
        if self.is_spectator or not self.battle_engine:
            return
        
        if self.verbose:
            seq = msg.get('sequence_number', '?')
            print(f"[{self.name}] [VERBOSE] Received CALCULATION_CONFIRM (seq={seq})")
        
        # CALCULATION_CONFIRM is just an acknowledgment that the opponent also confirmed
        # The turn should already be switched when we received their calculation report
        # This is just for synchronization - no need to confirm again
        
        # Check for game over
        if self.battle_engine.state == BattleState.GAME_OVER:
            self._send_game_over()
    
    def _handle_resolution_request(self, msg: Dict):
        """Handle resolution request message."""
        if self.is_spectator or not self.battle_engine:
            return
        
        if self.verbose:
            seq = msg.get('sequence_number', '?')
            print(f"[{self.name}] [VERBOSE] Received RESOLUTION_REQUEST (seq={seq})")
        
        # Re-evaluate and accept opponent's calculation for resolution
        calculation = {
            'attacker': msg.get('attacker', ''),
            'move_used': msg.get('move_used', ''),
            'damage_dealt': int(msg.get('damage_dealt', 0)),
            'defender_hp_remaining': int(msg.get('defender_hp_remaining', 0)),
            'remaining_health': int(msg.get('remaining_health', 0)),
            'status_message': f"{msg.get('attacker', '')} used {msg.get('move_used', '')}!"
        }
        
        print(f"[{self.name}] Resolving calculation mismatch - accepting opponent's calculation.")
        
        # Accept opponent's calculation and set both calculations to match
        # This ensures confirm_calculation() will work
        is_opponent_attack = calculation['attacker'] == self.battle_engine.opponent_pokemon_name
        self.battle_engine.apply_calculation(calculation, not is_opponent_attack)
        
        # Also set the other calculation to match so confirm_calculation works
        if is_opponent_attack:
            # Opponent attacked, so set my_calculation to match
            self.battle_engine.my_calculation = calculation.copy()
        else:
            # I attacked, so set opponent_calculation to match
            self.battle_engine.opponent_calculation = calculation.copy()
        
        # Display battle statistics with the resolved calculation
        self._display_battle_stats(calculation)
        
        if self.on_battle_update:
            status_msg = calculation.get('status_message', '')
            if status_msg:
                self.on_battle_update(status_msg)
        
        # Confirm and switch turns (should work now that both calculations match)
        if self.battle_engine.confirm_calculation():
            # Display turn completion message
            if self.battle_engine.state != BattleState.GAME_OVER:
                print(f"[{self.name}] Turn complete. {'Your turn!' if self.battle_engine.is_my_turn else 'Waiting for opponent...'}")
            
            # Check for game over
            if self.battle_engine.state == BattleState.GAME_OVER:
                self._send_game_over()
        else:
            print(f"[{self.name}] Warning: Could not confirm calculation after resolution.")
    
    def _handle_game_over(self, msg: Dict):
        """Handle game over message."""
        winner = msg.get('winner', '')
        loser = msg.get('loser', '')
        
        if self.verbose:
            seq = msg.get('sequence_number', '?')
            print(f"[{self.name}] [VERBOSE] Received GAME_OVER (seq={seq})")
        
        # Display final battle state
        if self.battle_engine:
            print("\n" + "=" * 70)
            print("💀 BATTLE ENDED 💀")
            print("=" * 70)
            print(f"🏆 Winner: {winner}")
            print(f"💔 Loser: {loser} (fainted)")
            print("-" * 70)
            print("FINAL STATUS:")
            my_hp = self.battle_engine.my_current_hp
            my_max_hp = self.battle_engine.my_pokemon.hp
            opp_hp = self.battle_engine.opponent_current_hp
            opp_max_hp = self.battle_engine.opponent_pokemon.hp
            print(self._hp_bar(my_hp, my_max_hp, self.battle_engine.my_pokemon_name, True))
            print(self._hp_bar(opp_hp, opp_max_hp, self.battle_engine.opponent_pokemon_name, False))
            print("=" * 70 + "\n")
        
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
            if winner == self.battle_engine.my_pokemon_name:
                loser = self.battle_engine.opponent_pokemon_name
            else:
                loser = self.battle_engine.my_pokemon_name
            
            # Display fainting message
            print("\n" + "=" * 70)
            print(f"💀 {loser} has fainted!")
            print(f"🏆 {winner} wins the battle!")
            print("=" * 70 + "\n")
            
            seq = self.reliability.get_next_sequence_number()
            game_over_msg = MessageProtocol.create_game_over(winner, loser, seq)
            self.reliability.send_message(game_over_msg, seq)
            
            if self.verbose:
                print(f"[{self.name}] [VERBOSE] Sent GAME_OVER (seq={seq}): Winner={winner}, Loser={loser}")

