"""
A python file used to store all global constants used in this project.

This includes colours, a common button style, text, the actual board size of the Othello
game as well as simple dictionaries to convert internal token representations into either
their opposite or full names.

As well as this it also holds constants for general file handling and durations for videos/Gifs.
"""

DGREEN = (5, 196, 107)
DBLACK = (30, 39, 46)
LBLUE = (87, 95, 207)
DBLUE = (60, 64, 198)
DRED = (255, 63, 52)
LGREEN = (11, 232, 129)
LGREY = (210, 218, 226)
DGREY = (128, 142, 155)
LBLACK = (72, 84, 96)
WHITE = (240, 240, 235)
YELLOW = (241, 196, 15)

BUTTON_STYLE = {"hover_colour": DBLUE, "clicked_colour": DBLUE, "clicked_font_colour": LBLACK,
                "hover_font_colour": DBLACK}

HELP_TEXT1 = "Othello is a strategy board game for two players (Black and White), played on an 8 by 8 board. The game traditionally begins with four pieces placed in the middle of the board as shown below with Black moving first."
HELP_TEXT2 = "Black must place a black piece on the board, in such a way that there is at least one straight (horizontal, vertical, or diagonal) occupied line between the new piece and another black piece, with one or more contiguous white pieces between them. In this starting position, Black has 4 options, indicated by the translucent pieces."
HELP_TEXT3 = "After placing the piece, Black flips all white pieces lying on a straight line between the new piece and any existing black pieces. All flipped pieces are now black. If Black decides to place a piece in the topmost location, one white piece gets flipped, and the board now looks like this."
HELP_TEXT4 = "Now White plays. This player operates under the same rules, with the roles reversed: White lays down a white piece, causing black pieces to flip. Possibilities at this time would be as such."
HELP_TEXT5 = "Players alternate taking turns. If a player does not have any valid moves, play passes back to the other player. When neither player can move, the game ends. A game of Othello may end before the board is completely filled.\nThe player with the most pieces on the board at the end of the game wins. If both players have the same number of pieces, then the game is a draw."

CONTEXT_BUTTON_TEXT0 = "Play against friends on the same computer."
CONTEXT_BUTTON_TEXT1 = "Play against an AI on various difficulty settings."
CONTEXT_BUTTON_TEXT2 = "Learn how to play so you can become a real pro."
CONTEXT_BUTTON_TEXT3 = "Look at or replay your previously played games."

WIN_MESSAGE_DEFAULT = "Congratulations! {} won with {} pieces and {} lost with {} pieces."
WIN_MESSAGE_AI_WIN = "Better luck next time! {} won with {} pieces and {} lost with {} pieces."
WIN_MESSAGE_AI_LOSS = "Congratulations you beat the AI! {} won with {} pieces and {} lost with {} pieces."
WIN_MESSAGE_CLOSE = WIN_MESSAGE_DEFAULT + " That was close!"
WIN_MESSAGE_CLOSE_AI_LOSS = WIN_MESSAGE_AI_LOSS + " That was close!"
WIN_MESSAGE_CLOSE_AI_WIN = WIN_MESSAGE_AI_WIN + " That was close!"
WIN_MESSAGE_TIE = "The game ended in a tie, you both had {} pieces."

BOARD_SIZE = 8
START_POS = {(BOARD_SIZE / 2, BOARD_SIZE / 2): "W", (BOARD_SIZE / 2 - 1, BOARD_SIZE / 2 - 1): "W",
             (BOARD_SIZE / 2 - 1, BOARD_SIZE / 2): "B", (BOARD_SIZE / 2, BOARD_SIZE / 2 - 1): "B"}
FLIP_RULE = {"W": "B", "B": "W", "E": "E"}
FLIP_LINES = [(-1, -1), (-1, 1), (1, -1), (1, 1), (1, 0), (-1, 0), (0, 1), (0, -1)]
FULL_NAME = {"W": "White", "B": "Black", "E": "Empty"}

XOR_INDICES = {"W": 1, "B": 2, "E": 0}

DIFFICULTY_TO_AI_CONFIG = {"Easy": (None, None), "Normal": (5,3), "Hard": (20, 3), "Insane": (24,10)}

# In y,x notation
SAFE_LINES = [(0, 0, (0, 1)), (0, 0, (1, 0)),
              (0, BOARD_SIZE - 1, (0, -1)), (0, BOARD_SIZE - 1, (1, 0)),
              (BOARD_SIZE - 1, 0, (0, 1)), (BOARD_SIZE - 1, 0, (0, 1)),
              (BOARD_SIZE - 1, BOARD_SIZE - 1, (0, -1)), (BOARD_SIZE - 1, BOARD_SIZE - 1, (-1, 0))]

LOCAL_IO = {"Click": 0, "Count": 1, "Print": 2, "Possible": 3, "Colour": 4, "End": 5, "MaxLine": 6,
            "PrintFull": 7, "Board": 8, "Loader": 9, "Fail": 10, "Loaded": 11, "Stop": 12, "Video": 13,
            "Winner": 14, "Net_Click": 15, "Net_Colour": 16, "Net_Send": 17, "Net_End": 18, "Net_Loaded": 19}

SAVE_DIR = "sav"
SAVE_SUFFIX = ".oth"

RES_DIR = "res"

CONFETTI_DURATION = 1 / 30

MULTICAST_GROUP = "224.1.1.1"
MULTICAST_PORT = 1785

TCP_DATA_TYPE = {"Opponent_Colour": b'0', "Move": b'1'}

LOADING_CONN_MESSAGE = "Awaiting connection..."

CON_ERROR_MESSAGE = "Connection error: Peer Disconnected."

LOAD_DURATION = [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]

