import queue

from MzingaShared.Core import EnumUtils

MaxStack = 5

_neighbor_deltas = [
    [0, 1, -1],
    [1, 0, -1],
    [1, -1, 0],
    [0, -1, 1],
    [-1, 0, 1],
    [-1, 1, 0]
]


class Position:
    _local_cache = None
    _shared_cache = {}

    def __init__(self, stack, x=None, y=None, z=None, q=None, r=None):
        if stack < 0:
            raise ValueError("Stack must be >= 0.")
        self.stack = stack

        if x is not None:
            self.x = x
            self.y = y
            self.z = z
            self.q = x
            self.r = z
        elif q is not None:
            self.x = q
            self.z = r
            self.y = 0 - q - r

    def __eq__(self, other):
        if self is None:
            return other is None
        return self.equals(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.get_hash_code()

    def __repr__(self):
        rep_strs = [str(self.x), ',', str(self.y), ',', str(self.z), ',', str(self.stack)]

        if self.stack > 0:
            return "".join(rep_strs)
        return "".join(rep_strs[0:-2:])

    def equals(self, pos):
        if pos is None:
            return False
        return self.q == pos.q and self.r == pos.r and self.stack == pos.stack

    def cache_lookup(self, index):
        if not self._local_cache:
            if self not in list(self._shared_cache.keys()):
                self._shared_cache[self] = [0] * (EnumUtils.NumDirections + 2)
                self._local_cache = self._shared_cache[self]
            else:
                self._local_cache = self._shared_cache[self]

        # created_new = False
        new = False
        cached = self._local_cache[index]
        is_pos = isinstance(cached, Position)
        if is_pos:
            new = cached == self

        if (not is_pos) or new:
            if index < EnumUtils.NumDirections:
                cx = self.x + _neighbor_deltas[index][0]
                cy = self.y + _neighbor_deltas[index][1]
                cz = self.z + _neighbor_deltas[index][2]
                self._local_cache[index] = Position(stack=0, x=cx, y=cy, z=cz)
                # created_new = True
            elif index == EnumUtils.NumDirections:  # Above
                self._local_cache[index] = Position(stack=self.stack + 1, x=self.x, y=self.y, z=self.z)
                # created_new = True
            elif index == EnumUtils.NumDirections + 1 and self.stack > 0:  # Below
                self._local_cache[index] = Position(stack=self.stack - 1, x=self.x, y=self.y, z=self.z)
                # created_new = True

        return self._local_cache[index]

    def is_touching(self, piece_position):
        if not piece_position:
            raise ValueError("piece_position")

        for i in range(EnumUtils.NumDirections):
            if self.neighbour_at(i) == piece_position:
                return True
        return False

    def neighbour_at(self, direction):
        if isinstance(direction, int):
            direction = direction % EnumUtils.NumDirections
            return self.cache_lookup(direction)
        else:
            return self.neighbour_at(EnumUtils.Directions[direction])

    def get_above(self):
        return self.cache_lookup(EnumUtils.NumDirections)

    def get_below(self):
        return self.cache_lookup(EnumUtils.NumDirections + 1)

    def get_hash_code(self):
        hash_code = 17 * 31 + self.q
        hash_code = hash_code * 31 + self.r
        hash_code = hash_code * 31 + self.stack
        return hash_code


def get_unique_positions(count, max_stack=MaxStack):
    if count < 1:
        raise ValueError("count must be >= 1")

    positions = queue.Queue()
    positions.put(Position(stack=0, x=0, y=0, z=0))
    result = set()

    while not positions.empty():
        pos = positions.get()
        for i in range(EnumUtils.NumDirections + 2):
            if len(result) < count:
                neighbor = pos.cache_lookup(i)

                old_len = len(result)
                if neighbor:
                    result.add(neighbor)

                if len(result) > old_len and neighbor and neighbor.stack < max_stack:
                    positions.put(neighbor)
    return result


origin = Position(stack=0, x=0, y=0, z=0)


def parse(position_string):
    status, board_position = try_parse(position_string)
    if status:
        return board_position
    raise ValueError("Invalid position string.")


def try_parse(position_string):
    try:
        if not position_string or position_string.isspace():
            return True, None

        position_string = position_string.strip()
        split = list(filter(None, position_string.split(',')))

        if len(split) == 2:
            position = Position(stack=0, q=split[0], r=split[1])
            return True, position
        elif len(split) >= 3:
            stack = int(split[3]) if len(split) > 3 else 0
            position = Position(stack=stack, x=int(split[0]), y=int(split[1]), z=int(split[2]))
            return True, position
    except ValueError:
        return False, None
