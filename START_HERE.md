# 🎮 START HERE - PokeProtocol Tutorial

Welcome! This guide will teach you how to run the Pokemon Battle Protocol step by step.

## ✅ Prerequisites Check

Your system is ready! ✅
- Python 3.14.0 installed
- All required files present
- Pokemon data loaded successfully

## 📖 Choose Your Learning Path

### 🚀 Quick Start (5 minutes)
→ Read `QUICK_START.md` - Get playing immediately!

### 📚 Detailed Guide (15 minutes)  
→ Read `HOW_TO_RUN.md` - Learn everything in detail

### 🔍 Understanding the Code
→ Read `README.md` - Learn about the architecture

---

## 🎯 The Simplest Way to Run

### You Need 2 Terminal Windows!

**Window 1 - HOST (Player 1):**
```bash
python main.py --name Player1 --host --port 8888 --pokemon Pikachu
```

**Window 2 - JOINER (Player 2):**
```bash
python main.py --name Player2 --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
```

**Then in Window 1, type:**
```
attack Thunderbolt
```

**Then in Window 2, type:**
```
attack Flamethrower
```

**That's it! You're battling!** ⚡🔥

---

## 📁 File Guide

| File | Purpose |
|------|---------|
| `main.py` | **START HERE** - The main program you run |
| `QUICK_START.md` | Quick reference guide |
| `HOW_TO_RUN.md` | Detailed tutorial |
| `README.md` | Technical documentation |
| `pokemon.csv` | Pokemon data (required) |

---

## 🎓 Step-by-Step Learning

### Level 1: Basic Battle (Start Here!)
1. Open 2 terminals
2. Run host in terminal 1
3. Run joiner in terminal 2
4. Type `attack Thunderbolt` in terminal 1
5. Type `attack Flamethrower` in terminal 2
6. Keep taking turns!

### Level 2: Chat Feature
1. Type `chat Hello!` in either terminal
2. The other player sees your message

### Level 3: Verbose Mode
1. Add `--verbose` to your commands
2. See all the technical protocol messages
3. Understand how the protocol works

### Level 4: Spectator Mode
1. Open a 3rd terminal
2. Run: `python main.py --name Spectator --port 8890 --connect 127.0.0.1:8888 --spectator`
3. Watch the battle without participating!

---

## 🆘 Need Help?

### Common Commands

**Check if Python works:**
```bash
python --version
```

**List available Pokemon:**
```bash
python main.py --pokemon InvalidName
```

**See help:**
```bash
python main.py --help
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "Address already in use" | Use `--port 9999` instead |
| "Pokemon not found" | Check spelling: `Pikachu`, `Charmander` |
| "Connection refused" | Start host first, then joiner |
| Python not found | Try `python3` or `py` |

---

## 🎮 Example Battle Flow

```
Terminal 1 (Host)          Terminal 2 (Joiner)
─────────────────          ──────────────────
$ python main.py...        $ python main.py...
[Player1]>                  [Player2]>
                            (waiting...)
attack Thunderbolt ────────> (receives attack)
[BATTLE] Pikachu used...    [BATTLE] Pikachu used...
                            attack Flamethrower ────>
                            [BATTLE] Charmander used...
(receives attack) <──────── [BATTLE] Charmander used...
attack Thunder ────────────> (receives attack)
[BATTLE] Pikachu used...    [BATTLE] Pikachu used...
                            [GAME OVER] Winner: Pikachu
[GAME OVER] Winner: Pikachu
```

---

## 📝 Next Steps

1. ✅ Read `QUICK_START.md` for immediate play
2. ✅ Try a battle with a friend
3. ✅ Experiment with different Pokemon
4. ✅ Enable verbose mode to see how it works
5. ✅ Read the code to understand the implementation

---

## 🎉 You're Ready!

Everything is set up and working. Just open 2 terminals and start battling!

**Remember:**
- Host goes first
- Take turns attacking
- Use `quit` to exit
- Have fun! 🎮

---

**Questions?** Check `HOW_TO_RUN.md` for detailed explanations!

