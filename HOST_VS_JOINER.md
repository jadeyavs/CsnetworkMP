# Host vs Joiner - Quick Explanation

## 🎯 Simple Answer

**JOINER = The player who CONNECTS to the host**

## 📋 Visual Guide

```
┌─────────────────────────────────────────────────────────┐
│  TERMINAL 1 - HOST (Player 1)                           │
│  ────────────────────────────────────────────────────   │
│  Command:                                                │
│    python main.py --name Player1 --host --port 8888     │
│                                                          │
│  Key: Has --host flag                                    │
│  Role: Waits for someone to connect                     │
│  Goes: FIRST in battle                                  │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │
                        │ Connects to
                        │
┌───────────────────────┴─────────────────────────────────┐
│  TERMINAL 2 - JOINER (Player 2)                        │
│  ────────────────────────────────────────────────────  │
│  Command:                                               │
│    python main.py --name Player2 --port 8889          │
│    --connect 127.0.0.1:8888                             │
│                                                         │
│  Key: Has --connect flag (NO --host flag)              │
│  Role: Connects to the host                            │
│  Goes: SECOND in battle                                │
└────────────────────────────────────────────────────────┘
```

## 🔑 Key Differences

| Feature | HOST | JOINER |
|---------|------|--------|
| **Flag** | `--host` | `--connect IP:PORT` |
| **Starts** | First (waits for connection) | Second (connects to host) |
| **Port** | Usually 8888 | Different port (8889, 8890, etc.) |
| **Goes first?** | ✅ Yes | ❌ No (waits for host) |

## 📝 Commands Side-by-Side

### HOST (Terminal 1)
```bash
python main.py --name Player1 --host --port 8888 --pokemon Pikachu
```
**Has:** `--host` flag  
**Does:** Waits for someone to connect  
**Attacks:** First

### JOINER (Terminal 2)
```bash
python main.py --name Player2 --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
```
**Has:** `--connect` flag (NO `--host`)  
**Does:** Connects to the host  
**Attacks:** Second (after host)

## 🎮 Battle Flow

1. **Host starts** → Waits on port 8888
2. **Joiner connects** → Sends connection request to host
3. **Host responds** → Battle begins
4. **Host attacks first** → "attack Thunderbolt"
5. **Joiner attacks second** → "attack Flamethrower"
6. **Turns alternate** → Host → Joiner → Host → Joiner...

## 💡 Memory Trick

- **HOST** = "I'm hosting the game" (like hosting a party)
- **JOINER** = "I'm joining someone else's game" (like joining a party)

## ⚠️ Common Mistake

**WRONG:**
```bash
# This is NOT a joiner - it's trying to be a host too!
python main.py --name Player2 --host --connect 127.0.0.1:8888
```

**CORRECT:**
```bash
# Joiner - NO --host flag, just --connect
python main.py --name Player2 --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
```

## 🎯 Quick Test

**Question:** Which one is the joiner?
- ✅ Has `--connect` flag → **JOINER**
- ✅ Has `--host` flag → **HOST**

## 📋 Complete Example

**Terminal 1 (HOST):**
```bash
python main.py --name Alice --host --port 8888 --pokemon Pikachu
```
Output: `[Alice] Listening on port 8888 as HOST`

**Terminal 2 (JOINER):**
```bash
python main.py --name Bob --port 8889 --connect 127.0.0.1:8888 --pokemon Charmander
```
Output: `[Bob] Battle initialized! Opponent goes first`

---

**Summary:** The JOINER is the one with `--connect` (and NO `--host` flag)!

