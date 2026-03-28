#!/usr/bin/env python3
"""
Halite Interactive Game Launcher.
Run this to play Halite manually.
"""

import sys
import argparse
from halite.play_halite import HalitePlayer


def main():
    parser = argparse.ArgumentParser(
        description="Play Halite manually",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python play.py              # Play on 16x16 board
  python play.py --size 8     # Play on 8x8 board
  python play.py --seed 42    # Play with specific seed
        """
    )
    parser.add_argument("--size", type=int, default=16,
                        help="Board size (default: 16, min: 8, max: 32)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducible games")

    args = parser.parse_args()

    # Validate board size
    if args.size < 8 or args.size > 32:
        print("Error: Board size must be between 8 and 32")
        sys.exit(1)

    print(f"\nStarting Halite game ({args.size}x{args.size})...")
    if args.seed:
        print(f"Seed: {args.seed}")
    print()

    player = HalitePlayer(board_size=args.size, seed=args.seed)
    player.run()


if __name__ == "__main__":
    main()
