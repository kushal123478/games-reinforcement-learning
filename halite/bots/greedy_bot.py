"""
Greedy collection agent for Halite.
This bot tries to collect nearby halite and return to base.
"""

import numpy as np
from kaggle_environments import make
from utils import find_direction_to_target, manhattan_distance


def greedy_bot(observation, config):
    """Greedy bot that collects halite."""
    board_size = config.board_size

    player_id = observation.player
    me = observation.players[player_id]
    ships = observation.ships[player_id]
    dropoff = observation.dropoffs[player_id]
    board = observation.halite

    actions = []

    for ship_id, ship in ships.items():
        ship_pos = (ship.x, ship.y)
        ship_halite = ship.halite

        # If ship is full or low on fuel, go to dropoff
        if ship_halite > 800 or (ship_halite > 100 and manhattan_distance(ship_pos, dropoff, board_size) > 10):
            direction = find_direction_to_target(ship_pos, dropoff, board_size)
            action = f"MOVE {ship_id} {direction}"
        else:
            # Find nearby halite cell
            best_cell = None
            best_value = 0

            # Check nearby cells
            for x in range(max(0, ship_pos[0] - 5), min(board_size, ship_pos[0] + 6)):
                for y in range(max(0, ship_pos[1] - 5), min(board_size, ship_pos[1] + 6)):
                    if (x, y) == ship_pos:
                        continue
                    halite_val = board[y][x]
                    if halite_val > best_value:
                        best_value = halite_val
                        best_cell = (x, y)

            if best_cell and best_value > 50:
                direction = find_direction_to_target(ship_pos, best_cell, board_size)
                action = f"MOVE {ship_id} {direction}"
            else:
                # Explore randomly
                action = f"MOVE {ship_id} {np.random.choice(['NORTH', 'SOUTH', 'EAST', 'WEST'])}"

        actions.append(action)

    # Spawn if we have enough halite
    if me.halite > 1000:
        actions.append("SPAWN")

    return "\n".join(actions)


if __name__ == "__main__":
    env = make("halite", configuration={"size": 16, "randomSeed": 42})

    def agent1(obs, config):
        return greedy_bot(obs, config)

    def agent2(obs, config):
        return greedy_bot(obs, config)

    env.reset()
    result = env.run([agent1, agent2])
    print("Greedy bot test successful!")
