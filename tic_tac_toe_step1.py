from dataclasses import dataclass, field, asdict
import redis.asyncio as redis
import json

redis_client = redis.Redis(
host = "ai.thewcl.com",
port = 6379,
password = "atmega328",
db = 1,
decode_responses=True 
)
REDIS_GAME_STATE_KEY = "tic_tac_toe:game_state:{team_number}"
team_number = 1
key = REDIS_GAME_STATE_KEY.format(team_number=team_number)

@dataclass
class TicTacToeBoard:
    state: str = field(default = "is_playing")
    player_turn: str = field(default = "x")
    positions: list[str] = field(default_factory = lambda: ["", "", "", "", "", "", "", "", ""]) # 3x3 grid, from index 0-8
    
    def is_my_turn(self, i_am): # checks if it is the player's turn, i_am is the player's mark (x or o)
        if self.state == "is_playing" and self.player_turn == i_am:
            return True
        else:
            return False

    def make_move(self, index: int):
        result = {"move success": False, "message": "", "board": self.positions.copy()} # Initializes success to False, message to empty string, and board to a copy of the current board state
        
        if self.state != "is_playing":
            result["message"] = "Game is not in progress."
            return result
        if index < 0 or index > 8:
            result["message"] = "Invalid position."
            return result
        if self.positions[index] != "":
            result["message"] = "Position already taken."
            return result
        
        self.positions[index] = self.player_turn
        result["board"] = self.positions.copy()

        if self.check_winner():
            result["move success"] = True
            result["message"] = f"Player {self.player_turn} wins!"
            return result
        if self.check_draw():
            result["move success"] = True
            result["message"] = "draw"
            return result
        self.switch_turn()
        result["move success"] = True
        result["message"] = f"Move accepted. Next turn: {self.player_turn}."
        return result   
           
    def check_winner(self):
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8], # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8], # columns
            [0, 4, 8], [2, 4, 6] # diagonals
        ]
        
        for combination in winning_combinations:
            a, b, c = combination
            if self.positions[a] != "" and self.positions[a] == self.positions[b] == self.positions[c]:
                self.state = f"{self.positions[a]}_won!"
                return True
        return False
    
    def check_draw(self):
        if "" not in self.positions:
            self.state = "draw"
            return True
        return False 
    
    def switch_turn(self):
        if self.player_turn == "x":
            self.player_turn = "o"
        elif self.player_turn == "o":
            self.player_turn = "x"
    
    def serialize(self):
        return json.dumps({ # convert dict to JSON str
        "state": self.state,
        "player_turn": self.player_turn,
        "positions": self.positions
    })
    
    async def save_to_redis(self, redis_client, key):
        json_string = self.serialize()
        board_dict = json.loads(json_string) # convert JSON str back to dict
        await redis_client.json().set(key, ".", board_dict) # figure out later

    @classmethod
    async def load_from_redis(cls, redis_client, key):
        data = await redis_client.json().get(key, ".") 
        if data is None:
            raise ValueError(f"No board data found in Redis for key: {key}")
        return cls(**data) # figure out later
    
    async def reset(self):
        self.state = "is_playing"
        self.player_turn = "x"
        self.positions = ["", "", "", "", "", "", "", "", ""] 
        await self.save_to_redis(redis_client, key)
        return {
            "status": "board_reset",
            "positions": self.positions,
            "player_turn": self.player_turn
        }
    
    def to_dict(self):
        board_to_dict = asdict(self)
        board_to_dict["positions"] = self.positions.copy() # This ensures that the positions list in the dictionary is a copy rather than a reference to the original list
        return board_to_dict