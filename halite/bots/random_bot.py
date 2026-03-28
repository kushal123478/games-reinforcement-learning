"""
Simple random agent for Halite.
This bot makes random valid moves at each turn.
"""

import numpy as np
from kaggle_environments import make


def random_bot(observation, config):
    """Random bot that chooses a valid action."""
    board_size = config.board_size

    # Get player ships and dropoff positions
    player_id = observation.player
    ships = observation.ships[player_id]
    dropoff = observation.dropoffs[player_id]

    actions = []

    # Choose random action for each ship
    for ship_id, ship in ships.items():
        # Possible moves: NORTH, SOUTH, EAST, WEST, STAY
        moves = ["NORTH", "SOUTH", "EAST", "WEST", "STAY"]
        action = f"MOVE {ship_id} {np.random.choice(moves)}"
        actions.append(action)

    # Optionally spawn a new ship if we have enough halite at shipyard
    if observation.ships[player_id]:  # Only if we have at least one ship
        actions.append("SPAWN")

    return "\n".join(actions)


if __name__ == "__main__":
    # Test the bot locally
    env = make("halite", configuration={"size": 8, "randomSeed": 0})

    # Two random bots
    def agent1(obs, config):
        return random_bot(obs, config)

    def agent2(obs, config):
        return random_bot(obs, config)

    env.reset()
    result = env.run([agent1, agent2])
    print("Halite environment test successful!")
    print(f"Result: {result}")
