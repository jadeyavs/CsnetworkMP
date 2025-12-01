"""
Message Protocol
Handles parsing and serialization of PokeProtocol messages.
"""
from typing import Dict, Optional, Any
import base64


class MessageProtocol:
    """Handles message parsing and serialization for PokeProtocol."""
    
    @staticmethod
    def parse_message(data: bytes) -> Dict[str, Any]:
        """Parse a message from bytes into a dictionary."""
        text = data.decode('utf-8')
        message = {}
        for line in text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                message[key] = value
        return message
    
    @staticmethod
    def serialize_message(message: Dict[str, Any]) -> bytes:
        """Serialize a message dictionary into bytes."""
        lines = []
        for key, value in message.items():
            lines.append(f"{key}: {value}")
        return '\n'.join(lines).encode('utf-8')
    
    @staticmethod
    def create_handshake_request(sequence_number: int = 0) -> bytes:
        """Create a HANDSHAKE_REQUEST message."""
        return MessageProtocol.serialize_message({
            'message_type': 'HANDSHAKE_REQUEST',
            'sequence_number': str(sequence_number)
        })
    
    @staticmethod
    def create_handshake_response(seed: int, sequence_number: int = 0) -> bytes:
        """Create a HANDSHAKE_RESPONSE message."""
        return MessageProtocol.serialize_message({
            'message_type': 'HANDSHAKE_RESPONSE',
            'seed': str(seed),
            'sequence_number': str(sequence_number)
        })
    
    @staticmethod
    def create_spectator_request(sequence_number: int = 0) -> bytes:
        """Create a SPECTATOR_REQUEST message."""
        return MessageProtocol.serialize_message({
            'message_type': 'SPECTATOR_REQUEST',
            'sequence_number': str(sequence_number)
        })
    
    @staticmethod
    def create_battle_setup(communication_mode: str, pokemon_name: str, 
                           stat_boosts: Dict[str, int], pokemon_data: Dict,
                           sequence_number: int = 0, seed: Optional[int] = None) -> bytes:
        """Create a BATTLE_SETUP message."""
        import json
        msg = {
            'message_type': 'BATTLE_SETUP',
            'communication_mode': communication_mode,
            'pokemon_name': pokemon_name,
            'stat_boosts': json.dumps(stat_boosts),
            'pokemon': json.dumps(pokemon_data),
            'sequence_number': str(sequence_number)
        }
        if seed is not None:
            msg['seed'] = str(seed)
        return MessageProtocol.serialize_message(msg)
    
    @staticmethod
    def create_attack_announce(move_name: str, sequence_number: int) -> bytes:
        """Create an ATTACK_ANNOUNCE message."""
        return MessageProtocol.serialize_message({
            'message_type': 'ATTACK_ANNOUNCE',
            'move_name': move_name,
            'sequence_number': str(sequence_number)
        })
    
    @staticmethod
    def create_defense_announce(sequence_number: int) -> bytes:
        """Create a DEFENSE_ANNOUNCE message."""
        return MessageProtocol.serialize_message({
            'message_type': 'DEFENSE_ANNOUNCE',
            'sequence_number': str(sequence_number)
        })
    
    @staticmethod
    def create_calculation_report(attacker: str, move_used: str, 
                                  remaining_health: int, damage_dealt: int,
                                  defender_hp_remaining: int, status_message: str,
                                  sequence_number: int) -> bytes:
        """Create a CALCULATION_REPORT message."""
        return MessageProtocol.serialize_message({
            'message_type': 'CALCULATION_REPORT',
            'attacker': attacker,
            'move_used': move_used,
            'remaining_health': str(remaining_health),
            'damage_dealt': str(damage_dealt),
            'defender_hp_remaining': str(defender_hp_remaining),
            'status_message': status_message,
            'sequence_number': str(sequence_number)
        })
    
    @staticmethod
    def create_calculation_confirm(sequence_number: int) -> bytes:
        """Create a CALCULATION_CONFIRM message."""
        return MessageProtocol.serialize_message({
            'message_type': 'CALCULATION_CONFIRM',
            'sequence_number': str(sequence_number)
        })
    
    @staticmethod
    def create_resolution_request(attacker: str, move_used: str, 
                                 damage_dealt: int, defender_hp_remaining: int,
                                 sequence_number: int) -> bytes:
        """Create a RESOLUTION_REQUEST message."""
        return MessageProtocol.serialize_message({
            'message_type': 'RESOLUTION_REQUEST',
            'attacker': attacker,
            'move_used': move_used,
            'damage_dealt': str(damage_dealt),
            'defender_hp_remaining': str(defender_hp_remaining),
            'sequence_number': str(sequence_number)
        })
    
    @staticmethod
    def create_game_over(winner: str, loser: str, sequence_number: int) -> bytes:
        """Create a GAME_OVER message."""
        return MessageProtocol.serialize_message({
            'message_type': 'GAME_OVER',
            'winner': winner,
            'loser': loser,
            'sequence_number': str(sequence_number)
        })
    
    @staticmethod
    def create_chat_message(sender_name: str, content_type: str, 
                           message_text: str = None, sticker_data: str = None,
                           sequence_number: int = 0) -> bytes:
        """Create a CHAT_MESSAGE."""
        msg = {
            'message_type': 'CHAT_MESSAGE',
            'sender_name': sender_name,
            'content_type': content_type,
            'sequence_number': str(sequence_number)
        }
        if content_type == 'TEXT' and message_text:
            msg['message_text'] = message_text
        elif content_type == 'STICKER' and sticker_data:
            msg['sticker_data'] = sticker_data
        return MessageProtocol.serialize_message(msg)
    
    @staticmethod
    def create_host_announcement(host_name: str, port: int, pokemon_name: str = None) -> bytes:
        """Create a HOST_ANNOUNCEMENT for broadcast discovery."""
        msg = {
            'message_type': 'HOST_ANNOUNCEMENT',
            'host_name': host_name,
            'port': str(port)
        }
        if pokemon_name:
            msg['pokemon_name'] = pokemon_name
        return MessageProtocol.serialize_message(msg)
    
    @staticmethod
    def create_discovery_request(joiner_name: str) -> bytes:
        """Create a DISCOVERY_REQUEST to find hosts on the network."""
        return MessageProtocol.serialize_message({
            'message_type': 'DISCOVERY_REQUEST',
            'joiner_name': joiner_name
        })
    
    @staticmethod
    def create_discovery_response(host_name: str, port: int, pokemon_name: str = None) -> bytes:
        """Create a DISCOVERY_RESPONSE in reply to a discovery request."""
        msg = {
            'message_type': 'DISCOVERY_RESPONSE',
            'host_name': host_name,
            'port': str(port)
        }
        if pokemon_name:
            msg['pokemon_name'] = pokemon_name
        return MessageProtocol.serialize_message(msg)
    
    @staticmethod
    def create_ack(ack_number: int) -> bytes:
        """Create an ACK message."""
        return MessageProtocol.serialize_message({
            'message_type': 'ACK',
            'ack_number': str(ack_number)
        })
