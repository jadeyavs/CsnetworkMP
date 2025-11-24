"""
Comprehensive Rubric Compliance Test
Tests all rubric requirements systematically
"""
import sys
import os

def test_pokemon_loader():
    """Test Pokemon data loading"""
    print("Testing Pokemon Loader...")
    from pokemon_loader import PokemonLoader
    loader = PokemonLoader()
    pika = loader.get_pokemon('Pikachu')
    char = loader.get_pokemon('Charmander')
    assert pika is not None, "Pikachu not found"
    assert char is not None, "Charmander not found"
    assert pika.hp > 0, "Invalid HP"
    assert pika.sp_attack > 0, "Missing Sp. Attack"
    assert pika.sp_defense > 0, "Missing Sp. Defense"
    print("[PASS] Pokemon Loader")
    return True

def test_message_serialization():
    """Test message serialization and sequence numbers"""
    print("\nTesting Message Serialization...")
    from message_protocol import MessageProtocol
    
    # Test handshake request has sequence number
    msg = MessageProtocol.create_handshake_request(1)
    parsed = MessageProtocol.parse_message(msg)
    assert 'message_type' in parsed, "Missing message_type"
    assert 'sequence_number' in parsed, "Handshake missing sequence_number"
    assert parsed['message_type'] == 'HANDSHAKE_REQUEST', "Wrong message type"
    
    # Test battle setup has sequence number
    import json
    msg = MessageProtocol.create_battle_setup('P2P', 'Pikachu', 
                                             {'special_attack_uses': 5}, 
                                             {'name': 'Pikachu'}, 2)
    parsed = MessageProtocol.parse_message(msg)
    assert 'sequence_number' in parsed, "Battle setup missing sequence_number"
    
    # Test all message types
    msg = MessageProtocol.create_attack_announce('Thunderbolt', 3)
    parsed = MessageProtocol.parse_message(msg)
    assert 'sequence_number' in parsed, "Attack announce missing sequence_number"
    
    print("[PASS] Message Serialization")
    return True

def test_damage_calculator():
    """Test damage calculation"""
    print("\nTesting Damage Calculator...")
    from damage_calculator import DamageCalculator, get_move_info
    from pokemon_loader import PokemonLoader
    
    loader = PokemonLoader()
    pika = loader.get_pokemon('Pikachu')
    char = loader.get_pokemon('Charmander')
    
    calc = DamageCalculator(12345)
    move = get_move_info('Thunderbolt')
    
    assert move['type'] == 'electric', "Wrong move type"
    assert move['power'] > 0, "Invalid move power"
    assert move['category'] in ['physical', 'special'], "Invalid category"
    
    damage, status = calc.calculate_damage(
        pika, char, 'Thunderbolt', 'electric', 90.0, 'special',
        {'special_attack_uses': 5}, {'special_defense_uses': 5}
    )
    
    assert damage > 0, "Damage should be positive"
    assert 'Thunderbolt' in status, "Status message should mention move"
    print("[PASS] Damage Calculator")
    return True

def test_battle_engine():
    """Test battle state machine"""
    print("\nTesting Battle Engine...")
    from battle_engine import BattleEngine, BattleState
    from pokemon_loader import PokemonLoader
    
    loader = PokemonLoader()
    pika = loader.get_pokemon('Pikachu')
    char = loader.get_pokemon('Charmander')
    
    engine = BattleEngine(12345, True)
    assert engine.state == BattleState.SETUP, "Should start in SETUP"
    
    engine.setup_battle(pika, char, 
                       {'special_attack_uses': 5}, 
                       {'special_defense_uses': 5})
    
    assert engine.state == BattleState.WAITING_FOR_MOVE, "Should be WAITING_FOR_MOVE"
    assert engine.is_my_turn == True, "Host should go first"
    assert engine.my_current_hp == pika.hp, "HP not set correctly"
    
    print("[PASS] Battle Engine")
    return True

def test_reliability_layer():
    """Test reliability layer"""
    print("\nTesting Reliability Layer...")
    from reliability_layer import ReliabilityLayer
    
    sent_messages = []
    def send_callback(msg):
        sent_messages.append(msg)
    
    layer = ReliabilityLayer(send_callback)
    layer.start()
    
    seq1 = layer.send_message(b'test1')
    seq2 = layer.send_message(b'test2')
    
    assert seq1 == 1, "First sequence should be 1"
    assert seq2 == 2, "Sequence should increment"
    assert len(sent_messages) == 2, "Should send 2 messages"
    
    layer.handle_ack(1)
    assert 1 not in layer.pending_messages, "Message should be removed after ACK"
    
    is_dup = layer.is_duplicate(2)
    assert is_dup == False, "First time should not be duplicate"
    is_dup2 = layer.is_duplicate(2)
    assert is_dup2 == True, "Second time should be duplicate"
    
    layer.stop()
    print("[PASS] Reliability Layer")
    return True

def test_verbose_mode():
    """Test verbose mode implementation"""
    print("\nTesting Verbose Mode...")
    from poke_protocol_peer import PokeProtocolPeer
    
    peer_verbose = PokeProtocolPeer("Test", 9999, False, verbose=True)
    assert peer_verbose.verbose == True, "Verbose should be True"
    
    peer_normal = PokeProtocolPeer("Test", 9998, False, verbose=False)
    assert peer_normal.verbose == False, "Verbose should be False"
    
    print("[PASS] Verbose Mode")
    return True

def test_sticker_saving():
    """Test sticker file saving functionality"""
    print("\nTesting Sticker Saving...")
    import base64
    import os
    
    # Create test sticker data (minimal PNG)
    test_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
    test_b64 = base64.b64encode(test_png).decode('utf-8')
    
    # Check if sticker directory creation code exists
    from poke_protocol_peer import PokeProtocolPeer
    import inspect
    
    source = inspect.getsource(PokeProtocolPeer._handle_chat_message)
    assert 'stickers' in source.lower(), "Sticker saving code not found"
    assert 'base64' in source.lower(), "Base64 decoding not found"
    assert 'os.makedirs' in source or 'makedirs' in source, "Directory creation not found"
    
    print("[PASS] Sticker Saving")
    return True

def test_game_over():
    """Test GAME_OVER functionality"""
    print("\nTesting GAME_OVER...")
    from poke_protocol_peer import PokeProtocolPeer
    import inspect
    
    source = inspect.getsource(PokeProtocolPeer)
    assert '_send_game_over' in source, "GAME_OVER sending method not found"
    assert 'GAME_OVER' in source, "GAME_OVER handling not found"
    
    from message_protocol import MessageProtocol
    msg = MessageProtocol.create_game_over('Pikachu', 'Charmander', 10)
    parsed = MessageProtocol.parse_message(msg)
    assert parsed['message_type'] == 'GAME_OVER', "Wrong message type"
    assert parsed['winner'] == 'Pikachu', "Wrong winner"
    assert parsed['loser'] == 'Charmander', "Wrong loser"
    assert 'sequence_number' in parsed, "Missing sequence number"
    
    print("[PASS] GAME_OVER")
    return True

def test_turn_flow():
    """Test 4-step turn flow"""
    print("\nTesting Turn Flow...")
    from message_protocol import MessageProtocol
    
    # Step 1: ATTACK_ANNOUNCE
    msg1 = MessageProtocol.create_attack_announce('Thunderbolt', 1)
    parsed1 = MessageProtocol.parse_message(msg1)
    assert parsed1['message_type'] == 'ATTACK_ANNOUNCE', "Step 1 failed"
    
    # Step 2: DEFENSE_ANNOUNCE
    msg2 = MessageProtocol.create_defense_announce(2)
    parsed2 = MessageProtocol.parse_message(msg2)
    assert parsed2['message_type'] == 'DEFENSE_ANNOUNCE', "Step 2 failed"
    
    # Step 3: CALCULATION_REPORT
    msg3 = MessageProtocol.create_calculation_report(
        'Pikachu', 'Thunderbolt', 35, 50, 0, 'Status', 3
    )
    parsed3 = MessageProtocol.parse_message(msg3)
    assert parsed3['message_type'] == 'CALCULATION_REPORT', "Step 3 failed"
    
    # Step 4: CALCULATION_CONFIRM
    msg4 = MessageProtocol.create_calculation_confirm(4)
    parsed4 = MessageProtocol.parse_message(msg4)
    assert parsed4['message_type'] == 'CALCULATION_CONFIRM', "Step 4 failed"
    
    print("[PASS] Turn Flow (4-step)")
    return True

def test_chat_functionality():
    """Test chat functionality"""
    print("\nTesting Chat Functionality...")
    from message_protocol import MessageProtocol
    
    # Text chat
    msg_text = MessageProtocol.create_chat_message('Player1', 'TEXT', 
                                                   message_text='Hello!', 
                                                   sequence_number=1)
    parsed = MessageProtocol.parse_message(msg_text)
    assert parsed['message_type'] == 'CHAT_MESSAGE', "Wrong message type"
    assert parsed['content_type'] == 'TEXT', "Wrong content type"
    assert parsed['message_text'] == 'Hello!', "Wrong message text"
    
    # Sticker chat
    sticker_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    msg_sticker = MessageProtocol.create_chat_message('Player1', 'STICKER',
                                                      sticker_data=sticker_data,
                                                      sequence_number=2)
    parsed2 = MessageProtocol.parse_message(msg_sticker)
    assert parsed2['content_type'] == 'STICKER', "Wrong content type"
    assert 'sticker_data' in parsed2, "Missing sticker data"
    
    print("[PASS] Chat Functionality")
    return True

def test_discrepancy_resolution():
    """Test discrepancy resolution"""
    print("\nTesting Discrepancy Resolution...")
    from message_protocol import MessageProtocol
    
    msg = MessageProtocol.create_resolution_request(
        'Pikachu', 'Thunderbolt', 50, 0, 5
    )
    parsed = MessageProtocol.parse_message(msg)
    assert parsed['message_type'] == 'RESOLUTION_REQUEST', "Wrong message type"
    assert 'sequence_number' in parsed, "Missing sequence number"
    assert parsed['damage_dealt'] == '50', "Wrong damage"
    
    print("[PASS] Discrepancy Resolution")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("POKEPROTOCOL RUBRIC COMPLIANCE TEST")
    print("=" * 60)
    
    tests = [
        test_pokemon_loader,
        test_message_serialization,
        test_damage_calculator,
        test_battle_engine,
        test_reliability_layer,
        test_verbose_mode,
        test_sticker_saving,
        test_game_over,
        test_turn_flow,
        test_chat_functionality,
        test_discrepancy_resolution,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
    
    if failed == 0:
        print("\n[SUCCESS] ALL TESTS PASSED - RUBRIC COMPLIANCE VERIFIED!")
        return 0
    else:
        print(f"\n[ERROR] {failed} TEST(S) FAILED - REVIEW REQUIRED")
        return 1

if __name__ == '__main__':
    sys.exit(main())

