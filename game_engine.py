from tic_tac_toe_step1 import TicTacToeBoard, redis_client, REDIS_GAME_STATE_KEY
import argparse
import asyncio

key = REDIS_GAME_STATE_KEY

try:
    board = await TicTacToeBoard.load_from_redis() # Try to load existing board from Redis, or create a new one if not found
except ValueError:
    print("Create new board")
    board = TicTacToeBoard()
    board.save_to_redis(redis_client, key)

parser = argparse.ArgumentParser(description="Tic Tac Toe CLI") # Create argument parser
parser.add_argument("--player", choices=["x", "o"], help="Your player symbol (x or o)") # Add player argument with choices x and o
parser.add_argument("--reset", action="store_true", help="Reset the game board") # Add reset argument that resets the board

args = parser.parse_args()

if args.reset:
    board = TicTacToeBoard()
    board.reset(redis_client, key)
    print("Board reset.")
    exit()

player_symbol = args.player

if board is None:
    board = TicTacToeBoard()

if board.is_my_turn(player_symbol):
    print(board.positions)
    index = int(input(f"Player {player_symbol}, enter position (0-8): "))
    board.player_symbol = player_symbol  # You may still need this so `make_move` knows which mark to place
    board.make_move(index)
    board.save_to_redis(redis_client, key)
else:
    print(f"It is not your turn. Current turn: {board.player_turn}")

if board.state == "draw" or board.state == "x_won!" or board.state == "o_won!":
    print(f"Game ended: {board.state}")
    board.reset()
    print("Starting a new game...")