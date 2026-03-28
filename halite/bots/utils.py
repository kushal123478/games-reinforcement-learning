"""
Utility functions for Halite bots.
"""

import numpy as np


def manhattan_distance(pos1, pos2, board_size):
    """Calculate Manhattan distance with wrapping."""
    dx = abs(pos1[0] - pos2[0])
    dy = abs(pos1[1] - pos2[1])
    dx = min(dx, board_size - dx)
    dy = min(dy, board_size - dy)
    return dx + dy


def get_neighbors(pos, board_size):
    """Get valid neighboring positions."""
    x, y = pos
    neighbors = []
    for dx, dy, direction in [(0, -1, "NORTH"), (0, 1, "SOUTH"),
                               (1, 0, "EAST"), (-1, 0, "WEST")]:
        nx = (x + dx) % board_size
        ny = (y + dy) % board_size
        neighbors.append(((nx, ny), direction))
    return neighbors


def get_nearest_target(ship_pos, targets, board_size):
    """Find nearest target to ship."""
    if not targets:
        return None
    nearest = min(targets, key=lambda t: manhattan_distance(ship_pos, t, board_size))
    return nearest


def find_direction_to_target(ship_pos, target_pos, board_size):
    """Find direction to move towards target."""
    sx, sy = ship_pos
    tx, ty = target_pos

    # Calculate wrapped distances
    x_dist = tx - sx
    y_dist = ty - sy

    # Prefer wrapping if it's shorter
    if abs(x_dist) > board_size / 2:
        x_dist = -(board_size - abs(x_dist)) * (1 if x_dist > 0 else -1)
    if abs(y_dist) > board_size / 2:
        y_dist = -(board_size - abs(y_dist)) * (1 if y_dist > 0 else -1)

    # Choose direction with largest absolute distance
    if abs(x_dist) >= abs(y_dist):
        return "EAST" if x_dist > 0 else "WEST"
    else:
        return "SOUTH" if y_dist > 0 else "NORTH"
