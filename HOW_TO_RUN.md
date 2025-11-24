# How to Run PokeProtocol

This guide will teach you how to run the PokeProtocol implementation step by step.

## Prerequisites

1. **Python 3.7 or higher** - Check your version:
   ```bash
   python --version
   ```
   or
   ```bash
   python3 --version
   ```

2. **Pokemon CSV file** - Make sure `pokemon.csv` is in the same directory as the code files.

## Quick Start Guide

### Step 1: Open Terminal/Command Prompt

- **Windows**: Press `Win + R`, type `cmd` or `powershell`, press Enter
- **Mac/Linux**: Open Terminal application

### Step 2: Navigate to the Project Directory

```bash
cd "C:\Users\Jade Yabut\Desktop\Cursor\CsnetworkMP"
```

Or if you're on Mac/Linux:
```bash
cd /path/to/CsnetworkMP
```

### Step 3: Verify Files are Present

List the files to make sure everything is there:
```bash
dir
```
(Windows) or
```bash
ls
```
(Mac/Linux)

You should see files like:
- `main.py`
- `poke_protocol_peer.py`
- `pokemon_loader.py`
- `message_protocol.py`
- `battle_engine.py`
- `damage_calculator.py`
- `reliability_layer.py`
- `pokemon.csv`
- `README.md`

## Running the Application

You need **at least 2 terminal windows** to test the battle (one for Host, one for Joiner).

### Scenario 1: Running as HOST (Player 1)

**In Terminal Window 1:**

```bash
python main.py --name Alice --host --port 8888 --pokemon Pikachu
```

**What this does:**
- `--name Alice` - Sets your player name to "Alice"
- `--host` - Makes you the host (you go first)
- `--port 8888` - Listens on port 8888
- `--pokemon Pikachu` - You're using Pikachu

**Expected output:**
```
[Alice] Listening on port 8888 as HOST
[Alice] Received HANDSHAKE_REQUEST, sent HANDSHAKE_RESPONSE with seed 12345
[Alice] Sent BATTLE_SETUP with Pikachu
[Alice] Received BATTLE_SETUP: Opponent is Charmander
[Alice] Battle initialized! You go first

Commands:
  attack <move_name> - Attack with a move
  chat <message> - Send a text chat message
  pokemon <name> - Set your Pokemon
  quit - Exit the application

[Alice]>
```

### Scenario 2: Running as JOINER (Player 2)

**In Terminal Window 2:**

```bash
python main.py --name Bob --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
```

**What this does:**
- `--name Bob` - Sets your player name to "Bob"
- `--port 8889` - Uses a different port (can't use 8888, it's taken by host)
- `--connect 127.0.0.1:8888` - Connects to host at localhost port 8888
- `--pokemon Charmander` - You're using Charmander

**Expected output:**
```
[Bob] Listening on port 8889
[Bob] Sent HANDSHAKE_REQUEST to ('127.0.0.1', 8888)
[Bob] Received HANDSHAKE_RESPONSE with seed 12345
[Bob] Sent BATTLE_SETUP with Charmander
[Bob] Received BATTLE_SETUP: Opponent is Pikachu
[Bob] Battle initialized! Opponent goes first

Commands:
  attack <move_name> - Attack with a move
  chat <message> - Send a text message
  pokemon <name> - Set your Pokemon
  quit - Exit the application

[Bob]>
```

## Playing the Game

### Basic Commands

Once both players are connected, you can use these commands:

#### 1. Attack Command

**Host (Alice) goes first:**
```
[Alice]> attack Thunderbolt
```

**Output:**
```
[BATTLE] Pikachu used Thunderbolt! It was super effective!
[Alice]>
```

**Then Joiner (Bob) can attack:**
```
[Bob]> attack Flamethrower
```

**Output:**
```
[BATTLE] Charmander used Flamethrower!
[Bob]>
```

#### 2. Chat Command

Send a text message:
```
[Alice]> chat Good luck!
```

The other player will see:
```
[CHAT] Alice: Good luck!
```

#### 3. Check Available Moves

Common moves you can use:
- `Thunderbolt`, `Thunder` (Electric)
- `Flamethrower`, `Ember` (Fire)
- `Water Gun`, `Hydro Pump` (Water)
- `Vine Whip`, `Solar Beam` (Grass)
- `Tackle`, `Quick Attack` (Normal)
- `Bite` (Dark)
- `Scratch` (Normal)

#### 4. Quit Command

Exit the game:
```
[Alice]> quit
```

## Advanced Usage

### Verbose Mode

To see all protocol messages (useful for debugging):

**Host:**
```bash
python main.py --name Alice --host --port 8888 --pokemon Pikachu --verbose
```

**Joiner:**
```bash
python main.py --name Bob --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander --verbose
```

**What you'll see in verbose mode:**
```
[Alice] [VERBOSE] Sent HANDSHAKE_RESPONSE (seq=1) with seed 12345
[Alice] [VERBOSE] Received HANDSHAKE_REQUEST, sent HANDSHAKE_RESPONSE (seq=1) with seed 12345
[Alice] [VERBOSE] Sent BATTLE_SETUP (seq=2) with Pikachu
[Alice] [VERBOSE] Received BATTLE_SETUP (seq=2): Opponent is Charmander
[Alice] [VERBOSE] Sent ATTACK_ANNOUNCE (seq=3): Thunderbolt
[Alice] [VERBOSE] Sent ACK (ack=3) for message type ATTACK_ANNOUNCE
```

### Running as Spectator

Watch a battle without participating:

**Terminal Window 3:**
```bash
python main.py --name Spectator --port 8890 --connect 127.0.0.1:8888 --spectator
```

Spectators can:
- See all battle messages
- Send and receive chat messages
- Cannot attack or influence the battle

### Using Different Pokemon

You can use any Pokemon from the CSV file. Some examples:
- `Pikachu`
- `Charmander`
- `Squirtle`
- `Bulbasaur`
- `Charizard`
- `Blastoise`
- `Venusaur`

**To see available Pokemon:**
```bash
python main.py --pokemon InvalidName
```

This will show the first 20 available Pokemon.

## Troubleshooting

### Problem: "Address already in use"

**Solution:** The port is already taken. Use a different port:
```bash
python main.py --name Player --host --port 9999 --pokemon Pikachu
```

### Problem: "Connection refused"

**Solution:** 
1. Make sure the host is running first
2. Check the IP address (use `127.0.0.1` for localhost)
3. Make sure the port number matches

### Problem: "Pokemon not found"

**Solution:** 
- Check spelling (case-sensitive)
- Use the exact name from the CSV
- Try: `Pikachu`, `Charmander`, `Squirtle`, `Bulbasaur`

### Problem: "Not your turn to attack"

**Solution:** Wait for your turn. The host goes first, then turns alternate.

### Problem: Python not found

**Solution:**
- Try `python3` instead of `python`
- Make sure Python is installed and in your PATH
- On Windows, you might need to use `py` instead:
  ```bash
  py main.py --name Alice --host --port 8888 --pokemon Pikachu
  ```

## Testing Checklist

1. ✅ Host starts and listens on port
2. ✅ Joiner connects to host
3. ✅ Both exchange Pokemon data
4. ✅ Host can attack first
5. ✅ Joiner can attack after host
6. ✅ Chat messages work
7. ✅ Game ends when HP reaches 0
8. ✅ Verbose mode shows all messages

## Example Full Battle

**Terminal 1 (Host):**
```bash
python main.py --name Alice --host --port 8888 --pokemon Pikachu
[Alice]> attack Thunderbolt
[BATTLE] Pikachu used Thunderbolt! It was super effective!
[Alice]> attack Thunder
[BATTLE] Pikachu used Thunder!
[Alice]> quit
```

**Terminal 2 (Joiner):**
```bash
python main.py --name Bob --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
[Bob]> attack Flamethrower
[BATTLE] Charmander used Flamethrower!
[Bob]> attack Ember
[BATTLE] Charmander used Ember!
[Bob]> quit
```

## Next Steps

1. Try different Pokemon combinations
2. Test chat functionality
3. Enable verbose mode to see protocol details
4. Test with multiple spectators
5. Try connecting from different machines (use actual IP instead of 127.0.0.1)

Happy battling! 🎮⚡🔥💧🌿

