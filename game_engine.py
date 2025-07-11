from tic_tac_toe_step1 import TicTacToeBoard, redis_client, REDIS_GAME_STATE_KEY
import argparse
import asyncio

CHANNEL = "ttt_game_state_changed" 
key = REDIS_GAME_STATE_KEY

async def handle_board_state(player_symbol):
    board = await TicTacToeBoard.load_from_redis(redis_client, key)
    if board.is_my_turn(player_symbol):
        print(board.positions)
        index = int(input(f"Player {player_symbol}, enter position (0-8): "))
        board.make_move(index)
        await board.save_to_redis(redis_client, key)
        
        if board.state in ["draw", "x_won!", "o_won!"]:
            print(f"Game ended: {board.state}")
            await redis_client.publish(CHANNEL, "updated")
            await board.reset()
            print("Board reset. Waiting for next game...")
        else:
            await redis_client.publish(CHANNEL, "updated")
    else:
        print(f"Not your turn. Current turn: {board.player_turn}")

async def listen_for_updates(player_symbol):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CHANNEL)
    print(f"Subscribed and listening for updates on channel: {CHANNEL}")
    
    board = await TicTacToeBoard.load_from_redis(redis_client, key)
    if board.is_my_turn(player_symbol):
        await handle_board_state(player_symbol)
    
    async for message in pubsub.listen():
        if message['type'] == 'message':
            print(f"Received update: {message['data']}")
            board = await TicTacToeBoard.load_from_redis(redis_client, key)
            if board.is_my_turn(player_symbol):
                await handle_board_state(player_symbol)

async def main():
    parser = argparse.ArgumentParser(description="Tic Tac Toe CLI") # Create argument parser
    parser.add_argument("--player", choices=["x", "o"], help="Your player symbol (x or o)") # Add player argument with choices x and o
    parser.add_argument("--reset", action="store_true", help="Reset the game board") # Add reset argument that resets the board
    args = parser.parse_args()

    if args.reset:
        board = TicTacToeBoard()
        await board.reset()
        print("Board reset.")
        exit()

    if args.player is None:
        print("Please specify a player (x or o)")
        exit()
    player_symbol = args.player
    
    try:
        board = await TicTacToeBoard.load_from_redis(redis_client, key) # Try to load existing board from Redis, or create a new one if not found
    except ValueError:
        print("Create new board")
        board = TicTacToeBoard()
        await board.save_to_redis(redis_client, key)

    await listen_for_updates(player_symbol)

if __name__ == "__main__":
    asyncio.run(main())