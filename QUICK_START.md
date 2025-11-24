# Quick Start Guide - PokeProtocol

## 🚀 Fastest Way to Test

### Step 1: Open TWO Terminal Windows

You need 2 terminals because you need 2 players!

### Step 2: Terminal 1 - Start the HOST

Copy and paste this command:

```bash
python main.py --name Player1 --host --port 8888 --pokemon Pikachu
```

**You should see:**
```
[Player1] Listening on port 8888 as HOST

Commands:
  attack <move_name> - Attack with a move
  chat <message> - Send a text chat message
  pokemon <name> - Set your Pokemon
  quit - Exit the application

[Player1]>
```

### Step 3: Terminal 2 - Connect as JOINER

Copy and paste this command:

```bash
python main.py --name Player2 --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
```

**You should see:**
```
[Player2] Listening on port 8889
[Player2] Opponent is Pikachu
[Player2] Battle initialized! Opponent goes first

Commands:
  attack <move_name> - Attack with a move
  chat <message> - Send a text chat message
  pokemon <name> - Set your Pokemon
  quit - Exit the application

[Player2]>
```

### Step 4: Start Battling!

**In Terminal 1 (Player1 - Host):**
```
[Player1]> attack Thunderbolt
```

**In Terminal 2 (Player2 - Joiner):**
```
[Player2]> attack Flamethrower
```

**Keep taking turns until someone wins!**

---

## 📋 Command Reference

| Command | What it does | Example |
|---------|-------------|---------|
| `attack <move>` | Attack with a move | `attack Thunderbolt` |
| `chat <message>` | Send a chat message | `chat Good luck!` |
| `pokemon <name>` | Change Pokemon | `pokemon Charizard` |
| `quit` | Exit the game | `quit` |

---

## 🎮 Available Moves

Try these moves:
- `Thunderbolt` ⚡
- `Flamethrower` 🔥
- `Water Gun` 💧
- `Solar Beam` 🌿
- `Tackle` 👊
- `Bite` 🦷

---

## 🔍 Verbose Mode (Optional)

Want to see all the technical details? Add `--verbose`:

**Terminal 1:**
```bash
python main.py --name Player1 --host --port 8888 --pokemon Pikachu --verbose
```

**Terminal 2:**
```bash
python main.py --name Player2 --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander --verbose
```

---

## ❓ Common Issues

**"Address already in use"**
→ Use a different port: `--port 9999`

**"Pokemon not found"**
→ Check spelling: `Pikachu`, `Charmander`, `Squirtle`, `Bulbasaur`

**"Connection refused"**
→ Make sure Terminal 1 (host) is running first!

**Python not found?**
→ Try `python3` or `py` instead of `python`

---

## 🎯 Full Example

**Terminal 1:**
```bash
python main.py --name Alice --host --port 8888 --pokemon Pikachu
[Alice]> attack Thunderbolt
[BATTLE] Pikachu used Thunderbolt! It was super effective!
[Alice]> chat Nice move!
[Alice]> attack Thunder
[BATTLE] Pikachu used Thunder!
```

**Terminal 2:**
```bash
python main.py --name Bob --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
[Bob]> attack Flamethrower
[BATTLE] Charmander used Flamethrower!
[Bob]> chat Thanks!
[Bob]> attack Ember
[BATTLE] Charmander used Ember!
```

---

That's it! You're ready to battle! 🎮

For more details, see `HOW_TO_RUN.md`

