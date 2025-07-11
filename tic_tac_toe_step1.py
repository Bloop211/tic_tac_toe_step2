from dataclasses import dataclass, field
import redis.asyncio as redis
import json

redis_client = redis.Redis(
host = "ai.thewcl.com",
port = 6379,
password = "atmega328",
db = 1,
decode_responses=True 
)
REDIS_GAME_STATE_KEY = "tic_tac_toe:game_state"
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
        if self.state != "is_playing":
            print("Game is not in progress.")
            return
        if index < 0 or index > 8:
            print("Invalid position.")
            return
        if self.positions[index] != "":
            print("Position already taken.")
            return
        self.positions[index] = self.player_turn
        print(self.positions)
        if self.check_winner():
            print("win")
            return
        if self.check_draw():
            print("draw")
            return
        self.switch_turn()     
           
    def check_winner(self):
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8], # rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8], # columns
            [0, 4, 8], [2, 4, 6] # diagonals
        ]
        
        for combination in winning_combinations:
            a, b, c = combination
            if self.positions[a] != "" and self.positions[a] == self.positions[b] == self.positions[c]:
                print(f"Player {self.positions[a]} wins!")
                self.state = f"{self.positions[a]}_won!"
                return True
        return False
    
    def check_draw(self):
        if "" not in self.positions:
            print("Game is a draw!")
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
        await redis_client.json().set(key, ".", board_dict)

    @classmethod
    async def load_from_redis(cls, redis_client, key):
        data = await redis_client.json().get(key, ".")
        if data is None:
            raise ValueError(f"No board data found in Redis for key: {key}")
        return cls(**data)
    
    async def reset(self):
        self.state = "is_playing"
        self.player_turn = "x"
        self.positions = ["", "", "", "", "", "", "", "", ""] 
        await self.save_to_redis(redis_client, key)