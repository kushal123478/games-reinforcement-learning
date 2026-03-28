"""
Interactive CLI for playing Halite manually.
"""

from halite.game_engine import HaliteGame, Direction
from typing import Optional, Tuple
import sys


class HaliteVisualizer:
    """Handles board visualization and rendering."""

    # Unicode symbols for visualization
    SYMBOLS = {
        'player_0': '🟦',
        'player_1': '🟥',
        'halite': '◆',
        'empty': '·',
        'dropoff_0': '⊗',
        'dropoff_1': '⊗',
    }

    def __init__(self, game: HaliteGame):
        self.game = game

    def draw_board(self, player_view: int = 0):
        """Draw the game board from a player's perspective."""
        print("\n" + "=" * 60)
        print(f"TURN {self.game.turn}/{self.game.max_turns}")
        print("=" * 60)

        # Show scores
        scores = self.game.get_scores()
        for pid, halite in scores.items():
            print(f"Player {pid}: {halite} halite")
        print()

        # Build board representation
        board = [['·' for _ in range(self.game.board_size)] for _ in range(self.game.board_size)]

        # Add halite (show as numbers/colors based on amount)
        for y in range(self.game.board_size):
            for x in range(self.game.board_size):
                halite_amt = int(self.game.halite_board[y, x])
                if halite_amt > 400:
                    board[y][x] = '█'
                elif halite_amt > 300:
                    board[y][x] = '▓'
                elif halite_amt > 200:
                    board[y][x] = '▒'
                elif halite_amt > 100:
                    board[y][x] = '░'
                elif halite_amt > 0:
                    board[y][x] = '·'

        # Add dropoffs
        for pid, player in self.game.players.items():
            dx, dy = player.dropoff_position()
            board[dy][dx] = '◎'

        # Add ships (player 0 = blue, player 1 = red)
        for pid, player in self.game.players.items():
            for ship in player.ships.values():
                symbol = '●' if pid == player_view else '○'
                if board[ship.y][ship.x] not in ['◎']:  # Don't overwrite dropoff
                    board[ship.y][ship.x] = symbol

        # Print board
        print("  " + " ".join(f"{i:2}" for i in range(self.game.board_size)))
        for y, row in enumerate(board):
            print(f"{y:2} " + " ".join(row))
        print()

    def show_ship_info(self, player_id: int, ship_id: str):
        """Show detailed info about a ship."""
        player = self.game.players[player_id]
        if ship_id not in player.ships:
            print(f"❌ Ship {ship_id} not found!")
            return

        ship = player.ships[ship_id]
        print(f"\n📦 Ship {ship_id}:")
        print(f"   Position: ({ship.x}, {ship.y})")
        print(f"   Halite carried: {ship.halite}")
        print(f"   Dropoff at: {player.dropoff_position()}")

        # Calculate distance to dropoff
        dx = abs(ship.x - player.dropoff_x)
        dy = abs(ship.y - player.dropoff_y)
        dx = min(dx, self.game.board_size - dx)
        dy = min(dy, self.game.board_size - dy)
        dist = dx + dy
        print(f"   Distance to dropoff: {dist}")

    def show_help(self):
        """Show command help."""
        print("""
╔════════════════════════════════════════════════════════════╗
║                    HALITE COMMANDS                         ║
╚════════════════════════════════════════════════════════════╝

MOVEMENT:
  move <ship_id> <direction>    Move ship (NE, SW, EAST, WEST, STAY)
  Example: move 0-0 NORTH

ACTIONS:
  spawn                         Spawn new ship (costs 500 halite)
  info <ship_id>               Show ship details
  status                        Show all ships

VIEW:
  board                         Redraw board
  help                          Show this help
  quit                          Exit game

EXAMPLES:
  move 0-0 EAST                 Move ship 0-0 east
  spawn                         Create new ship at dropoff
  info 0-0                      Show info about ship 0-0
        """)


class HalitePlayer:
    """Main game loop and player interface."""

    def __init__(self, board_size: int = 16, seed: Optional[int] = None):
        self.game = HaliteGame(board_size=board_size, num_players=2, seed=seed)
        self.visualizer = HaliteVisualizer(self.game)
        self.player_id = 0  # Human player is always player 0

    def parse_command(self, cmd: str) -> Tuple[str, list]:
        """Parse player command."""
        parts = cmd.strip().lower().split()
        if not parts:
            return None, []
        return parts[0], parts[1:]

    def handle_move(self, args: list) -> bool:
        """Handle move command."""
        if len(args) < 2:
            print("❌ Usage: move <ship_id> <direction>")
            print("   Directions: NORTH, SOUTH, EAST, WEST, STAY")
            return False

        ship_id = args[0]
        direction_str = args[1].upper()

        try:
            direction = Direction[direction_str]
        except KeyError:
            print(f"❌ Invalid direction: {direction_str}")
            return False

        result = self.game.process_move(self.player_id, ship_id, direction)

        if result['success']:
            print(f"✓ Moved {ship_id} {direction_str}")
            print(f"  Position: ({result['position'][0]}, {result['position'][1]})")
            if result['collected'] > 0:
                print(f"  Collected: {result['collected']} halite")
            if result['deposited'] > 0:
                print(f"  Deposited: {result['deposited']} halite")
            return True
        else:
            print(f"❌ Move failed: {result['reason']}")
            return False

    def handle_spawn(self) -> bool:
        """Handle spawn command."""
        player = self.game.players[self.player_id]
        if player.halite < self.game.config['spawn_cost']:
            print(f"❌ Not enough halite! Need {self.game.config['spawn_cost']}, have {player.halite}")
            return False

        ship_id = self.game._spawn_ship(self.player_id)
        print(f"✓ Spawned new ship: {ship_id}")
        print(f"  Remaining halite: {player.halite}")
        return True

    def handle_info(self, args: list):
        """Handle info command."""
        if len(args) < 1:
            print("❌ Usage: info <ship_id>")
            return

        ship_id = args[0]
        self.visualizer.show_ship_info(self.player_id, ship_id)

    def handle_status(self):
        """Handle status command - show all ships."""
        player = self.game.players[self.player_id]
        print(f"\n📊 Your Ships (Player {self.player_id}):")
        print(f"   Total halite: {player.halite}")
        print(f"   Dropoff: {player.dropoff_position()}")
        print("\n   Ships:")
        for ship_id, ship in player.ships.items():
            print(f"   - {ship_id}: ({ship.x}, {ship.y}) carrying {ship.halite}")

    def play_turn(self):
        """Play a single turn."""
        print(f"\n🎮 Player {self.player_id} Turn")
        print("(Type 'help' for commands or 'next' to end turn)")

        player = self.game.players[self.player_id]
        moves_this_turn = 0

        while True:
            cmd = input("> ").strip()

            if not cmd:
                continue

            command, args = self.parse_command(cmd)

            if command == 'next':
                break
            elif command == 'quit':
                return False
            elif command == 'help':
                self.visualizer.show_help()
            elif command == 'board':
                self.visualizer.draw_board(self.player_id)
            elif command == 'status':
                self.handle_status()
            elif command == 'move':
                self.handle_move(args)
                moves_this_turn += 1
            elif command == 'spawn':
                self.handle_spawn()
                moves_this_turn += 1
            elif command == 'info':
                self.handle_info(args)
            else:
                print(f"❌ Unknown command: {command}")

        # Advance game turn after player move
        self.game.step()
        return True

    def run(self):
        """Main game loop."""
        print("""
╔════════════════════════════════════════════════════════════╗
║            WELCOME TO HALITE - MANUAL PLAY                ║
╚════════════════════════════════════════════════════════════╝

You are Player 0 (blue ●). Collect the most halite to win!

Basic strategy:
- Move ships to collect halite (◆ darkness = more halite)
- Return to your dropoff (◎) to deposit
- Spawn more ships to collect faster
- Each move is free, but planning is key

Type 'help' for all commands.
        """)

        while not self.game.game_over():
            self.visualizer.draw_board(self.player_id)
            if not self.play_turn():
                break

        # Game over
        print("\n" + "=" * 60)
        print("GAME OVER!")
        print("=" * 60)
        scores = self.game.get_scores()
        for pid, halite in scores.items():
            winner = "🏆 WINNER" if halite == max(scores.values()) else ""
            print(f"Player {pid}: {halite} halite {winner}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Play Halite manually")
    parser.add_argument("--size", type=int, default=16, help="Board size (default: 16)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()

    player = HalitePlayer(board_size=args.size, seed=args.seed)
    player.run()
