"""
Quick test to validate the game engine works.
"""

from halite.game_engine import HaliteGame, Direction

# Test game creation
game = HaliteGame(board_size=8, num_players=2, seed=42)
print('✓ Game created successfully')
print(f'  Board size: {game.board_size}x{game.board_size}')
print(f'  Players: {len(game.players)}')

# Test initial state
for pid, player in game.players.items():
    print(f'\nPlayer {pid}:')
    print(f'  Halite: {player.halite}')
    print(f'  Ships: {len(player.ships)}')
    print(f'  Dropoff: {player.dropoff_position()}')
    for ship_id, ship in player.ships.items():
        print(f'    - Ship {ship_id} at ({ship.x}, {ship.y})')

# Test a move
print('\n--- Testing Move ---')
result = game.process_move(0, '0-0', Direction.EAST)
print(f'Move successful: {result["success"]}')
print(f'New position: {result["position"]}')

print('\n✓ Game engine working!')
