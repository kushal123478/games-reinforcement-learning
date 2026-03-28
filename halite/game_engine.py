"""
Halite Game State Management.
Simulates the core game mechanics for manual play.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)
    STAY = (0, 0)


@dataclass
class Ship:
    """Represents a ship on the board."""
    id: str
    x: int
    y: int
    halite: int = 0
    alive: bool = True

    def position(self) -> Tuple[int, int]:
        return (self.x, self.y)


@dataclass
class Player:
    """Represents a player."""
    id: int
    halite: int
    ships: Dict[str, Ship]
    dropoffs: List[Tuple[int, int]]  # index 0 = original shipyard

    def dropoff_position(self) -> Tuple[int, int]:
        """Primary (original) dropoff — kept for compatibility."""
        return self.dropoffs[0]

    @property
    def dropoff_x(self) -> int:
        return self.dropoffs[0][0]

    @property
    def dropoff_y(self) -> int:
        return self.dropoffs[0][1]


class HaliteGame:
    """Core Halite game simulation."""

    def __init__(self, board_size: int = 16, num_players: int = 2, seed: Optional[int] = None):
        self.board_size = board_size
        self.num_players = num_players
        self.seed = seed
        self.turn = 0
        self.max_turns = 400

        # Game config - initialize first
        self._config = {
            'spawn_cost': 500,
            'convert_cost': 500,
            'move_cost': 1,  # Per cell
            'collect_rate': 0.25,
            'regen_rate': 0.02,
            'max_cell_halite': 500,
        }

        if seed is not None:
            np.random.seed(seed)

        # Initialize board
        self.halite_board = self._generate_halite_map()

        # Initialize players
        self.players: Dict[int, Player] = {}
        self._init_players()

    def _generate_halite_map(self) -> np.ndarray:
        """Generate random halite distribution."""
        board = np.random.randint(0, self.config['max_cell_halite'] + 1,
                                   (self.board_size, self.board_size))
        return board.astype(float)

    def _init_players(self):
        """Initialize players with starting ships and dropoffs at opposite corners."""
        positions = [
            (0, 0),
            (self.board_size - 1, self.board_size - 1),
            (0, self.board_size - 1),
            (self.board_size - 1, 0),
        ]

        for player_id in range(self.num_players):
            x, y = positions[player_id % len(positions)]

            ship = Ship(
                id=f"{player_id}-0",
                x=x,
                y=y,
                halite=0
            )

            self.players[player_id] = Player(
                id=player_id,
                halite=5000,  # Starting halite
                ships={ship.id: ship},
                dropoffs=[(x, y)],
            )

    @property
    def config(self) -> Dict:
        return self._config

    @config.setter
    def config(self, value):
        self._config = value
        self._config.update({'max_cell_halite': 500})

    def wrap_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Wrap coordinates to board boundaries."""
        return (x % self.board_size, y % self.board_size)

    def _move_ship(self, player_id: int, ship_id: str, direction: Direction) -> bool:
        """Move a ship in a direction. Returns True if successful."""
        player = self.players[player_id]
        if ship_id not in player.ships:
            return False

        ship = player.ships[ship_id]

        # Calculate new position
        dx, dy = direction.value
        new_x, new_y = self.wrap_coordinates(ship.x + dx, ship.y + dy)

        # Movement is free (unusual design!)
        ship.x = new_x
        ship.y = new_y

        return True

    def _collect_halite(self, player_id: int, ship_id: str) -> int:
        """Ship collects halite from current cell."""
        player = self.players[player_id]
        ship = player.ships[ship_id]

        cell_x, cell_y = ship.x, ship.y
        available = self.halite_board[cell_y, cell_x]

        # Collect 25% of available halite
        collected = int(available * self.config['collect_rate'])
        ship.halite += collected
        self.halite_board[cell_y, cell_x] -= collected

        return collected

    def _deposit_halite(self, player_id: int, ship_id: str) -> int:
        """Deposit halite at any of the player's dropoffs if ship is there."""
        player = self.players[player_id]
        ship = player.ships[ship_id]

        if (ship.x, ship.y) in player.dropoffs:
            deposited = ship.halite
            player.halite += deposited
            ship.halite = 0
            return deposited

        return 0

    def _spawn_ship(self, player_id: int) -> Optional[str]:
        """Spawn a new ship at dropoff if enough halite."""
        player = self.players[player_id]

        if player.halite < self.config['spawn_cost']:
            return None

        # Generate unique ship ID
        max_id = max([int(s.split('-')[1]) for s in player.ships.keys()] + [0])
        new_ship_id = f"{player_id}-{max_id + 1}"

        sx, sy = player.dropoffs[0]   # always spawn at original shipyard
        ship = Ship(id=new_ship_id, x=sx, y=sy, halite=0)

        player.ships[new_ship_id] = ship
        player.halite -= self.config['spawn_cost']

        return new_ship_id

    def convert_ship(self, player_id: int, ship_id: str) -> Optional[Tuple[int, int]]:
        """Convert a ship into a new dropoff point.

        Costs convert_cost halite from the bank, destroys the ship, and
        deposits any halite the ship was carrying.
        Returns the new dropoff position, or None on failure.
        """
        player = self.players[player_id]

        if ship_id not in player.ships:
            return None
        if player.halite < self.config['convert_cost']:
            return None

        ship = player.ships[ship_id]
        pos  = (ship.x, ship.y)

        if pos in player.dropoffs:
            return None   # already a dropoff here

        # Deposit any cargo the ship was carrying, then pay the cost
        player.halite += ship.halite
        player.halite -= self.config['convert_cost']

        del player.ships[ship_id]
        player.dropoffs.append(pos)

        return pos

    def process_move(self, player_id: int, ship_id: str, direction: Direction) -> Dict:
        """Process a ship move and return results."""
        player = self.players[player_id]

        if ship_id not in player.ships:
            return {'success': False, 'reason': 'Ship not found'}

        ship = player.ships[ship_id]

        # Move ship
        self._move_ship(player_id, ship_id, direction)

        # Collect halite
        collected = self._collect_halite(player_id, ship_id)

        # Try to deposit at dropoff
        deposited = self._deposit_halite(player_id, ship_id)

        return {
            'success': True,
            'position': (ship.x, ship.y),
            'collected': collected,
            'deposited': deposited,
            'ship_halite': ship.halite,
        }

    def step(self) -> bool:
        """Advance game by 1 turn. Returns True if game continues."""
        self.turn += 1
        return self.turn < self.max_turns

    def game_over(self) -> bool:
        """Check if game is over."""
        return self.turn >= self.max_turns

    def get_scores(self) -> Dict[int, int]:
        """Get current scores for all players."""
        return {pid: p.halite for pid, p in self.players.items()}

    def get_player_state(self, player_id: int) -> Dict:
        """Get full state for a player."""
        player = self.players[player_id]
        return {
            'id': player_id,
            'halite': player.halite,
            'ships': {
                sid: {
                    'x': ship.x,
                    'y': ship.y,
                    'halite': ship.halite,
                }
                for sid, ship in player.ships.items()
            },
            'dropoff': player.dropoff_position(),
        }
