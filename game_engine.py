from tic_tac_toe_step1 import TicTacToeBoard, redis_client, REDIS_GAME_STATE_KEY

board = TicTacToeBoard()
key = REDIS_GAME_STATE_KEY

player_symbol = input("Would you like to be x or o? ").lower().strip()

while board.state == "is_playing":
    if player_symbol in ["x", "o"]:
        if board.is_my_turn(player_symbol):
            index = int(input(f"Player {player_symbol}, enter a position (0-8): "))
            board.make_move(index)
            board.save_to_redis(redis_client, key)
        else:
            print(f"Not {player_symbol}'s turn.")
    else:
        print("Invalid player symbol.")
        player_symbol = input("Would you like to be x or o? ").lower().strip()

print(f"Game ended: {board.state}")