from dataclasses import dataclass, field
import redis
import json
import os

@dataclass
class TicTacToeBoard:
    state: str = field(default = "is_playing", init = False)
    player_turn: str = field(default = "x", init = False)
    positions: list[str] = field(default_factory = lambda: ["", "", "", "", "", "", "", "", ""]) # 3x3 grid, from index 0-8
    
    def is_my_turn(self, i_am): # checks if it is the player's turn, i_am is the player's mark (x or o)
        if self.state == "is_playing" and self.player_turn == i_am:
            print(i_am)
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
        self.positions[index] = self.player_symbol
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
        return json.dumps({
        "state": self.state,
        "player_turn": self.player_turn,
        "positions": self.positions
    })
    
    def save_to_redis(self, redis_client, key):
        json_string = self.serialize()
        board_dict = json.loads(json_string)
        redis_client.json().set(key, "$", board_dict)

    @classmethod
    def load_from_redis(cls):
        json_string = redis_client.get(key)
        board_dict = json.loads(json_string)
        return cls(**board_dict)
        
redis_host = os.environ.get("REDIS_HOST")
redis_port = os.environ.get("REDIS_PORT")
redis_password = os.environ.get("REDIS_PASSWORD")
redis_db = os.environ.get("REDIS_DB")

redis_client = redis.Redis(
host = redis_host,
port = redis_port,
password = redis_password,
db = redis_db
)
REDIS_GAME_STATE_KEY = "tic_tac_toe:game_state"
team_number = 1
key = REDIS_GAME_STATE_KEY.format(team_number=team_number)


print("Module-level redis_client:", redis_client)
print("Module-level key:", key)
