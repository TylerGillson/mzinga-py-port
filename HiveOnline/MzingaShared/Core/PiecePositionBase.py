from MzingaShared.Core.EnumUtils import piece_names, EnumUtils
from MzingaShared.Core import Position


class PiecePositionBase(object):
    __slots__ = "position", "colour", "bug_type", "_piece_name"

    def __init__(self):
        self.position = None
        self.colour = None
        self.bug_type = None
        self._piece_name = "INVALID"

    @property
    def piece_name(self):
        return self._piece_name

    @piece_name.setter
    def piece_name(self, value):
        self._piece_name = value

        if value != "INVALID":
            self.colour = EnumUtils.get_colour(value)
            self.bug_type = EnumUtils.get_bug_type(value)

    def parse(self, piece_string):
        if not self.try_parse(piece_string):
            raise ValueError("Unable to parse \"%s\"." % piece_string)

    def try_parse(self, piece_string):
        if not piece_string or piece_string.isspace():
            raise ValueError("Invalid piece_string")

        piece_string = piece_string.strip()

        try:
            sep = piece_string.find('[')
            name_string = piece_string[0:sep:]
            position_string = (piece_string[sep::]).replace('[', '').replace(']', '')
            self._piece_name = EnumUtils.parse_short_name(name_string)
            self.position = Position.parse(position_string)
            return True
        except ValueError:
            self._piece_name = "INVALID"
            self.position = None
            return False

    def __repr__(self):
        pos = self.position if self.position else ""
        return "%s[%s]" % (EnumUtils.get_short_name(self.piece_name), str(pos))
