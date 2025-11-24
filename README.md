# PokeProtocol - P2P Pokémon Battle Protocol

Implementation of the Peer-to-Peer Pokémon Battle Protocol (PokeProtocol) over UDP as specified in the RFC.

## Features

- **UDP-based P2P Communication**: Low-latency battle protocol using UDP with custom reliability layer
- **Turn-based Battle System**: Synchronized turn-based battles with explicit 4-step handshake per turn
- **Reliability Layer**: ACK-based message delivery with retransmission and sequence numbers
- **Damage Calculation**: Synchronized damage calculation with type effectiveness and stat boosts
- **Chat System**: Text and sticker support for peer-to-peer communication
- **Multiple Roles**: Support for Host, Joiner, and Spectator peers
- **Communication Modes**: P2P and Broadcast modes

## Architecture

### Core Components

1. **pokemon_loader.py**: Loads and manages Pokemon data from CSV
2. **message_protocol.py**: Message parsing and serialization
3. **reliability_layer.py**: UDP reliability with ACKs and retransmission
4. **damage_calculator.py**: Synchronized damage calculation engine
5. **battle_engine.py**: Battle state machine and turn management
6. **poke_protocol_peer.py**: Main peer implementation
7. **main.py**: Command-line interface

## Installation

Requires Python 3.7+

No external dependencies required (uses only standard library).

## Usage

### As Host

```bash
python main.py --name HostPlayer --host --port 8888 --pokemon Pikachu
```

### As Joiner

```bash
python main.py --name JoinerPlayer --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
```

### As Spectator

```bash
python main.py --name Spectator --port 8890 --connect 127.0.0.1:8888 --spectator
```

## Commands

Once connected, you can use these commands:

- `attack <move_name>` - Attack with a move (e.g., `attack Thunderbolt`)
- `chat <message>` - Send a text chat message
- `pokemon <name>` - Set your Pokemon (before battle starts)
- `quit` - Exit the application

## Verbose Mode

Use the `--verbose` flag to enable verbose mode, which shows all protocol messages including:
- All sent and received messages with sequence numbers
- ACK messages
- Retransmission attempts
- Reliability layer operations

Without verbose mode, only battle updates, chat messages, and errors are shown.

```bash
python main.py --name Player --host --pokemon Pikachu --verbose
```

## Sticker Support

When a sticker is received, it is automatically saved to the `stickers/` directory as a PNG file with a timestamp. The filename format is: `sticker_<sender>_<timestamp>.png`

## Available Moves

The implementation includes a basic move database. Common moves include:
- Thunderbolt, Thunder (Electric)
- Ember, Flamethrower (Fire)
- Water Gun, Hydro Pump (Water)
- Vine Whip, Solar Beam (Grass)
- Tackle, Quick Attack (Normal)
- Bite (Dark)
- Scratch (Normal)

## Protocol Flow

1. **Handshake**: Joiner sends HANDSHAKE_REQUEST, Host responds with HANDSHAKE_RESPONSE (includes seed)
2. **Battle Setup**: Both peers exchange BATTLE_SETUP with Pokemon data and stat boosts
3. **Turn Cycle**:
   - Attacker sends ATTACK_ANNOUNCE
   - Defender sends DEFENSE_ANNOUNCE
   - Both calculate damage independently
   - Both send CALCULATION_REPORT
   - Both send CALCULATION_CONFIRM if calculations match
   - If mismatch, RESOLUTION_REQUEST is sent
4. **Game Over**: When HP reaches 0, GAME_OVER message is sent

## Damage Calculation

The damage formula uses:
- Attacker's Attack/Sp. Attack stat (based on move category)
- Defender's Defense/Sp. Defense stat (based on move category)
- Move base power
- Type effectiveness (multiplied for dual-type Pokemon)
- Random factor (0.85-1.0)
- Stat boosts (consumable special attack/defense boosts)

## Reliability

- All messages include sequence numbers
- ACK messages confirm receipt
- Automatic retransmission on timeout (500ms default)
- Maximum 3 retries before connection failure
- Duplicate detection prevents message processing twice

## Notes

- The Pokemon CSV file (`pokemon.csv`) must be in the same directory
- Stat boosts are limited resources defined during setup (default: 5 uses each)
- Sticker support is implemented but requires Base64-encoded image data
- Broadcast mode is supported but requires network configuration

## Example Battle

```
Host: python main.py --name Alice --host --pokemon Pikachu
Joiner: python main.py --name Bob --connect 127.0.0.1:8888 --pokemon Charmander

[Alice]> attack Thunderbolt
[BATTLE] Pikachu used Thunderbolt! It was super effective!
[Bob]> attack Flamethrower
[BATTLE] Charmander used Flamethrower!
```

## License

This is an implementation of the PokeProtocol RFC specification.

