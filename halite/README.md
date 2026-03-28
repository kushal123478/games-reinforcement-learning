# Halite RL Environment

Competitive multi-agent reinforcement learning environment for Halite.

## Overview

Halite is a resource collection game where multiple agents (ships) compete to gather and return halite (a fictional resource) to their base. Your goal is to develop RL algorithms that can outcompete baseline strategies.

## Getting Started - Play the Game!

### Interactive Manual Play

To learn the game by playing it yourself:

```bash
python play.py --size 16
```

Start with a smaller board to learn:
```bash
python play.py --size 8 --seed 42
```

You control Player 0 (●) and the game displays the board state each turn.

**Board Visualization:**
- `█ ▓ ▒ ░ ·` = Halite density (darkest to lightest)
- `●` = Your ship (Player 0)
- `○` = Opponent ship (Player 1)
- `◎` = Dropoff/base

**Basic Commands:**
```
move 0-0 EAST           # Move ship 0-0 eastward
spawn                   # Create new ship (costs 500 halite)
info 0-0               # Show ship details
status                  # Show all your ships
board                   # Redraw the board
quit                    # Exit game
help                    # Show all commands
```

### Game Rules

- **Objective**: Collect the most halite
- **Movement**: Each move is FREE (no energy cost!)
- **Collection**: Ships collect 25% of halite in their cell per turn
- **Return**: Dock at your dropoff to deposit collected halite
- **Spawning**: Costs 500 halite, creates ships at your dropoff
- **Board**: Wraps at edges (toroidal)
- **Game Length**: 400 turns

## Project Structure

```
halite/
├── game_engine.py         # Core game simulation
├── play_halite.py         # Interactive CLI
├── bots/
│   ├── random_bot.py      # Random action baseline
│   ├── greedy_bot.py      # Greedy collection
│   └── utils.py           # Helper functions
├── logs/                  # Training logs
├── replays/               # Game recordings
└── README.md
```

Root level:
- `play.py` - Game launcher

## Strategy Tips

1. **Early**: Explore to find rich halite clusters (█ symbols)
2. **Multi-ship**: Spawn ships near high value areas
3. **Efficiency**: Balance collection time vs. return time
4. **Planning**: Movement is free—use positioning strategically
5. **Late game**: Defend high-value areas from opponents

## Playing Examples

### Start Game
```bash
$ python play.py --size 8
```

### First Turn
```
move 0-0 EAST              # Move ship east
✓ Moved 0-0 EAST
  Position: (1, 0)
  Collected: 45 halite

status
📊 Your Ships (Player 0):
   Total halite: 5045
   Ships:
   - 0-0: (1, 0) carrying 45
```

### Spawn & Strategy
```
move 0-0 EAST              # Collect more
move 0-0 EAST              # Keep collecting...
move 0-0 WEST              # Return to base
spawn                       # Create second ship
```

## Next Steps

1. **Play the game** - Understand mechanics hands-on
2. **Study baseline bots** - See `random_bot.py` and `greedy_bot.py`
3. **Run tournaments** - Compare strategies
4. **Implement RL** - Use game engine in training loops
5. **Compete** - Submit to Kaggle

## References

- **Original Game**: https://kaggle.com/c/halite
- **Kaggle Environments**: https://github.com/Kaggle/kaggle-environments
- **This Implementation**: Custom simulator for learning
