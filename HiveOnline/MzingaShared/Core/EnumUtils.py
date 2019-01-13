NumBugTypes = 5
NumColors = 2
NumDirections = 6
NumPieceNames = 22

Directions = {
    "Up": 0,
    "UpRight": 1,
    "DownRight": 2,
    "Down": 3,
    "DownLeft": 4,
    "UpLeft": 5,
}
DirectionsByInt = {v: k for k, v in Directions.items()}


Colours = {
    "White": 0,
    "Black": 1,
}
ColoursByInt = {v: k for k, v in Colours.items()}

BugTypes = {
    "QueenBee": 0,
    "Spider": 1,
    "Beetle": 2,
    "Grasshopper": 3,
    "SoldierAnt": 4,
}
BugTypesByInt = {v: k for k, v in BugTypes.items()}

PieceNames = {
    "INVALID": -1,
    "WhiteQueenBee": 0,
    "WhiteSpider1": 1,
    "WhiteSpider2": 2,
    "WhiteBeetle1": 3,
    "WhiteBeetle2": 4,
    "WhiteGrasshopper1": 5,
    "WhiteGrasshopper2": 6,
    "WhiteGrasshopper3": 7,
    "WhiteSoldierAnt1": 8,
    "WhiteSoldierAnt2": 9,
    "WhiteSoldierAnt3": 10,
    "BlackQueenBee": 11,
    "BlackSpider1": 12,
    "BlackSpider2": 13,
    "BlackBeetle1": 14,
    "BlackBeetle2": 15,
    "BlackGrasshopper1": 16,
    "BlackGrasshopper2": 17,
    "BlackGrasshopper3": 18,
    "BlackSoldierAnt1": 19,
    "BlackSoldierAnt2": 20,
    "BlackSoldierAnt3": 21,
}
PieceNamesByInt = {v: k for k, v in PieceNames.items()}

PieceShortNames = [
    "WQ",
    "WS1",
    "WS2",
    "WB1",
    "WB2",
    "WG1",
    "WG2",
    "WG3",
    "WA1",
    "WA2",
    "WA3",
    "BQ",
    "BS1",
    "BS2",
    "BB1",
    "BB2",
    "BG1",
    "BG2",
    "BG3",
    "BA1",
    "BA2",
    "BA3",
]

Rings = [
    ["Up", "UpRight", "DownRight", "Down", "DownLeft"],      # 6pc Up
    ["UpRight", "DownRight", "Down", "DownLeft", "UpLeft"],  # 6pc UpRight
    ["UpLeft", "Up", "UpRight", "DownRight", "Down"],        # 6pc UpLeft
    ["DownRight", "Down", "DownLeft", "UpLeft", "Up"],       # 6pc DownRight
    ["Down", "DownLeft", "UpLeft", "Up", "UpRight"],         # 6pc Down
    ["DownLeft", "UpLeft", "Up", "UpRight", "DownRight"],    # 6pc DownLeft
]


class EnumUtils:
    # DIRECTIONS
    @property
    def directions(self):
        return Directions.items()

    @staticmethod
    def left_of(direction):
        dir_val = (Directions[direction] + NumDirections - 1) % NumDirections
        return DirectionsByInt.get(dir_val)

    @staticmethod
    def right_of(direction):
        dir_val = (Directions[direction] + 1) % NumDirections
        return DirectionsByInt.get(dir_val)
    # END DIRECTIONS

    # PIECE NAMES
    @staticmethod
    def piece_names():
        return list(PieceNames.keys())

    @staticmethod
    def white_piece_names():
        return list(PieceNames.keys())[1:((len(PieceNames) - 1) // 2) + 1:]

    @staticmethod
    def black_piece_names():
        return list(PieceNames.keys())[(len(PieceNames) - 1) // 2::]

    @staticmethod
    def get_short_name(piece_name):
        if piece_name == "INVALID":
            return ""
        return PieceShortNames[PieceNames[piece_name]]

    @staticmethod
    def parse_short_name(name_string):
        if name_string is None or name_string.isspace():
            raise ValueError("Invalid name_string.")
        name_string = name_string.strip()

        for i in range(len(PieceShortNames)):
            if PieceShortNames[i] == name_string.upper():
                return PieceNamesByInt.get(i)
        raise ValueError("name_string not found.")
    # END PIECE NAMES

    # COLOURS
    @staticmethod
    def get_colour(piece_name):
        if piece_name not in PieceNames.keys() or piece_name == "INVALID":
            raise ValueError("Invalid piece_name.")

        for colour in Colours.keys():
            if colour in piece_name:
                return colour
    # END COLOURS

    # BUG TYPES
    @property
    def bug_types(self):
        return list(BugTypes.keys())

    @staticmethod
    def get_bug_type(piece_name):
        if piece_name not in PieceNames.keys() or piece_name == "INVALID":
            raise ValueError("Invalid piece_name.")

        for bug_type in BugTypes.keys():
            if bug_type in piece_name:
                return bug_type
