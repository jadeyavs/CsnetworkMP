# How to Get Joiner to Join the Battle

## ✅ Correct Way to Run Joiner

The joiner will **automatically** join the battle when you run it correctly. Here's how:

### Step-by-Step Process

**1. Start HOST first (Terminal 1):**
```bash
python main.py --name Player1 --host --port 8888 --pokemon Pikachu
```

**2. Start JOINER (Terminal 2):**
```bash
python main.py --name Player2 --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
```

**3. The joiner automatically:**
   - Sends handshake request
   - Receives handshake response
   - Sends battle setup
   - Receives host's battle setup
   - Battle begins!

## 🔍 What You Should See

### Terminal 1 (HOST) Output:
```
[Player1] Listening on port 8888 as HOST
[Player1] Received HANDSHAKE_REQUEST, sent HANDSHAKE_RESPONSE with seed 12345
[Player1] Sent BATTLE_SETUP with Pikachu
[Player1] Received BATTLE_SETUP: Opponent is Charmander
[Player1] Battle initialized! You go first

Commands:
  attack <move_name> - Attack with a move
  ...

[Player1]>
```

### Terminal 2 (JOINER) Output:
```
[Player2] Listening on port 8889
[Player2] Received HANDSHAKE_RESPONSE with seed 12345
[Player2] Sent BATTLE_SETUP with Charmander
[Player2] Received BATTLE_SETUP: Opponent is Pikachu
[Player2] Battle initialized! Opponent goes first

Commands:
  attack <move_name> - Attack with a move
  ...

[Player2]>
```

## ⚠️ Common Issues

### Issue 1: Joiner doesn't connect

**Problem:** Joiner shows "Listening on port..." but nothing happens

**Solution:**
1. Make sure HOST is running FIRST
2. Check the IP address is correct: `127.0.0.1:8888`
3. Check the port matches: Host uses `8888`, Joiner uses `8889` (different port!)

### Issue 2: "Connection refused"

**Problem:** Joiner can't connect to host

**Solution:**
- Start HOST first, wait for "Listening on port..."
- Then start JOINER
- Make sure IP and port are correct

### Issue 3: Battle doesn't start

**Problem:** Both connected but battle doesn't initialize

**Solution:**
- Make sure both have Pokemon set: `--pokemon Pikachu`
- Check that Pokemon names are correct (case-sensitive)
- Wait a moment for messages to exchange

## 🎯 Complete Working Example

**Terminal 1 (HOST):**
```bash
C:\Users\Jade Yabut\Desktop\Cursor\CsnetworkMP> python main.py --name Alice --host --port 8888 --pokemon Pikachu
[Alice] Listening on port 8888 as HOST

Commands:
  attack <move_name> - Attack with a move
  chat <message> - Send a text chat message
  pokemon <name> - Set your Pokemon
  quit - Exit the application

[Alice]>
```

**Terminal 2 (JOINER) - Run this AFTER Terminal 1:**
```bash
C:\Users\Jade Yabut\Desktop\Cursor\CsnetworkMP> python main.py --name Bob --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
[Bob] Listening on port 8889
[Bob] Opponent is Pikachu
[Bob] Battle initialized! Opponent goes first

Commands:
  attack <move_name> - Attack with a move
  chat <message> - Send a text chat message
  pokemon <name> - Set your Pokemon
  quit - Exit the application

[Bob]>
```

**Now both terminals should show the battle is ready!**

## 🔧 Troubleshooting Checklist

- [ ] HOST started first?
- [ ] HOST shows "Listening on port 8888 as HOST"?
- [ ] JOINER uses different port (8889, not 8888)?
- [ ] JOINER has `--connect 127.0.0.1:8888`?
- [ ] JOINER has NO `--host` flag?
- [ ] Both have Pokemon set with `--pokemon`?
- [ ] Pokemon names are spelled correctly?

## 💡 Verbose Mode for Debugging

If the joiner isn't connecting, use verbose mode to see what's happening:

**Terminal 1 (HOST):**
```bash
python main.py --name Player1 --host --port 8888 --pokemon Pikachu --verbose
```

**Terminal 2 (JOINER):**
```bash
python main.py --name Player2 --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander --verbose
```

You'll see all the protocol messages:
```
[Player2] [VERBOSE] Sent HANDSHAKE_REQUEST (seq=1) to ('127.0.0.1', 8888)
[Player2] [VERBOSE] Received HANDSHAKE_RESPONSE (seq=1) with seed 12345
[Player2] [VERBOSE] Sent BATTLE_SETUP (seq=2) with Charmander
[Player2] [VERBOSE] Received BATTLE_SETUP (seq=2): Opponent is Pikachu
```

## ✅ Success Indicators

You know the joiner joined successfully when you see:

1. **In HOST terminal:**
   - "Received BATTLE_SETUP: Opponent is [Pokemon]"
   - "Battle initialized! You go first"

2. **In JOINER terminal:**
   - "Opponent is [Pokemon]"
   - "Battle initialized! Opponent goes first"

3. **Both terminals show:**
   - The command prompt ready for input
   - You can type `attack` commands

## 🎮 Once Joined, Start Battling!

**HOST goes first:**
```
[Player1]> attack Thunderbolt
```

**Then JOINER:**
```
[Player2]> attack Flamethrower
```

The battle is now active! 🎉

