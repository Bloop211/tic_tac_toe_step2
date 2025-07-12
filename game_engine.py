# This file starts the game, manages player turns, saves game state to Redis, and listens for updates so players can take turns properly

from tic_tac_toe_step1 import TicTacToeBoard, redis_client, REDIS_GAME_STATE_KEY
import argparse
import asyncio
import json

CHANNEL = "ttt_game_state_changed"
team_number = 1
key = REDIS_GAME_STATE_KEY.format(team_number=team_number)  # This is the Redis key where we store the current board state so all players see the same game.

# Handle what happens when it's this player's turn: 1. Load board from Redis, 2. Ask for player input, 3. Make move, 4. Save updated board, 5. Notify other players if needed
async def handle_board_state(player_symbol):
    board = await TicTacToeBoard.load_from_redis(redis_client, key)
    if board.is_my_turn(player_symbol):
        print(json.dumps(board.to_dict(), indent=2))
        try:
            index = int(input(f"Player {player_symbol}, enter position (0-8): "))
        except ValueError:
            print("Invalid input. Please enter an integer between 0 and 8.")
            return

        result = board.make_move(index)
        print(result["message"])

        if result.get("move success"):
            await board.save_to_redis(redis_client, key)
            print(json.dumps(board.to_dict(), indent=2))

            if board.state in ["draw", "x_won!", "o_won!"]:
                await redis_client.publish(CHANNEL, "updated")  # Notify that game ended
                await board.reset()
                print("Board reset. Waiting for next game...")
                await redis_client.publish(CHANNEL, "updated")  # Notify that board is ready again!
            else:
                await redis_client.publish(CHANNEL, "updated") # Notify other players that the game state has changed so they can check if it's their turn.
    else:
        print(f"Not your turn. Current turn: {board.player_turn}")

# This function listens for game state updates on the Redis channel. When an "updated" message is received, check if it's this player's turn and handle their move.
async def listen_for_updates(player_symbol):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CHANNEL)
    print(f"Subscribed and listening for updates on channel: {CHANNEL}")

    while True:
        async for message in pubsub.listen():
            if message['type'] != 'message':
                continue

            msg_data = message['data']
            print(f"Received update: {msg_data}")

            # Only react if the message is exactly "updated"
            if msg_data == "updated":
                board = await TicTacToeBoard.load_from_redis(redis_client, key)
                if board.is_my_turn(player_symbol):
                    await handle_board_state(player_symbol)

async def main():
    parser = argparse.ArgumentParser(description="Tic Tac Toe CLI")
    parser.add_argument("--player", choices=["x", "o"], help="Your player symbol (x or o)")
    parser.add_argument("--reset", action="store_true", help="Reset the game board")
    args = parser.parse_args()

    if args.reset:
        board = TicTacToeBoard()
        await board.reset()
        print("Board reset.")
        return

    if args.player is None:
        print("Please specify a player (x or o)")
        return

    player_symbol = args.player

    try:
        board = await TicTacToeBoard.load_from_redis(redis_client, key)
    except ValueError:
        print("No existing board. Creating a new board...")
        board = TicTacToeBoard()
        await board.save_to_redis(redis_client, key)

    # Immediately handle first move if it's our turn
    board = await TicTacToeBoard.load_from_redis(redis_client, key)
    if board.is_my_turn(player_symbol):
        await handle_board_state(player_symbol)

    await listen_for_updates(player_symbol)

if __name__ == "__main__":
    asyncio.run(main())