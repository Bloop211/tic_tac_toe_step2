from tic_tac_toe_step1 import TicTacToeBoard, redis_client, REDIS_GAME_STATE_KEY
from fastapi import FastAPI, Body
app = FastAPI()

team_number = 1
key = REDIS_GAME_STATE_KEY.format(team_number=team_number)

@app.get("/state")
async def get_board_state():
    board = await TicTacToeBoard.load_from_redis(redis_client, key)
    return board.to_dict()

@app.post("/move")
async def make_move(data: dict = Body(...)): # Body accepts the request body as a dictionary
    player = data.get("player")
    index = data.get("index")
    board = await TicTacToeBoard.load_from_redis(redis_client, key)
    result = board.make_move(index, player)
    if result.get("move success"):
        await board.save_to_redis(redis_client, key)
    return result

@app.post("/reset")
async def reset_board():
    board = await TicTacToeBoard.load_from_redis(redis_client, key)
    await board.reset()
    return {"message": "Board reset."}
