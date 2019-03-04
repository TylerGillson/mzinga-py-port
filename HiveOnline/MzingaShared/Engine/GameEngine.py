import datetime
# import asyncio

from MzingaShared.Core.Board import InvalidMoveException
from MzingaShared.Core import GameBoard
from MzingaShared.Core.GameBoard import GameBoard as GameBoardCls
from MzingaShared.Core.Move import Move
from MzingaShared.Core import NotationUtils
from MzingaShared.Engine import GameEngineConfig
from Utils.Events import Broadcaster
from Utils.TaskQueue import TaskQueue

debug = True
# loop = asyncio.get_event_loop()


class GameEngine:
    game_id = ""
    config = None
    exit_requested = False

    _game_board = None
    _game_ai = None

    _ponder_queue = None
    _is_pondering = False

    _async_queue = None
    StartAsyncCommand = Broadcaster()

    cmd_dict = {
        "info": "self.info()",
        "help": "self.help()",
        "pass": "self.pass_turn()",
        "validmoves": "self.valid_moves()",
        "undo": "self.undo() if param_count == 0 else self.undo(split[1])",
        "exit": "self.exit()"
    }
    
    def __init__(self, game_id, config):
        if game_id is None or game_id.isspace():
            raise ValueError("id is None or whitespace")
        if config is None:
            raise ValueError("config is None")

        self.game_id = game_id
        self.config = config
        self.init_ai()
        self.exit_requested = False
        self.StartAsyncCommand.on_change += self.on_start_async_command

    def init_ai(self):
        self._game_ai = self.config.get_game_ai()

        if self.config.report_intermediate_best_moves:
            self._game_ai.best_move_found.on_change += self.on_best_move_found

    @staticmethod
    def on_best_move_found(args):
        if args is None:
            raise ValueError("args is None")
        if args.move is None:
            raise ValueError("Null move reported!")

        print("Current BMF (move/depth/score): %s;%d;%2f" % (args.move, args.depth, args.score))

    def parse_command(self, command):
        if command is None or command.isspace():
            raise ValueError("command is None")

        command = command.replace('\t', ' ')
        split = list(filter(None, command.split()))
        err = False
        err_msg = None

        try:
            cmd = split[0].lower()
            param_count = len(split) - 1
            # self.stop_ponder()

            if cmd == "bestmove":
                if param_count == 0:
                    return self.best_move()
                elif param_count >= 2 and split[1].lower() == "depth":
                    return self.best_move(max_depth=split[2])
                elif param_count >= 2 and split[1].lower() == "time":
                    return self.best_move(max_time=split[2])
                else:
                    self.raise_command_exception()
            elif cmd == "board":
                if param_count == 0:
                    return self.board()
                else:
                    return self.board("".join([s + " " for s in split[1:]]))
            elif cmd == "options":
                if param_count == 0:
                    return self.options_list()
                elif param_count >= 2 and split[1].lower() == "get":
                    return self.options_get(split[2])
                elif param_count >= 3 and split[1].lower() == "set":
                    return self.options_set(split[2], split[3])
                else:
                    self.raise_command_exception()
            elif cmd == "newgame":
                if param_count == 0:
                    return self.new_game()
                else:
                    return self.new_game(board_string=split[1])
            elif cmd == "play":
                self.raise_command_exception() if param_count < 1 else self.play("".join([s + " " for s in split[1:]]))
            else:
                return eval(self.cmd_dict[cmd])

        except KeyError:
            err_msg = "Invalid Command"
            print(err_msg)
            err = True
        except InvalidMoveException as ex:
            print("invalidmove %s", ex.message)
            err_msg = ex.message
            err = True
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
            err_msg = message
            err = True

        if not err:
            print("ok")
        else:
            return err, err_msg  # return error tuple to avoid crashing engine
        # self.start_ponder()

    def raise_command_exception(self):
        raise CommandException()

    def info(self):
        print("id %s" % self.game_id)

    @staticmethod
    def help():
        print("Available commands: ")
        print("info")
        print("help")
        print("board")
        print("newgame")
        print("play")
        print("pass")
        print("validmoves")
        print("bestmove")
        print("undo")
        print("options")
        print("exit")

    def board(self, board_string=None):
        if debug:
            if not (board_string is None or board_string.isspace()):
                self._game_board = GameBoardCls(board_string=board_string, game_type=self.config.game_type)
                self._game_ai.reset_caches()
        if self._game_board is None:
            raise NoBoardException
        print(self._game_board.to_game_string())

    def new_game(self, **kwargs):
        if kwargs:
            # First, try parsing the board string as boardspace notation:
            parsed, board = GameBoard.try_parse_game_string(kwargs.pop("board_string"), kwargs.pop("game_type"))

            # Otherwise, default to axial notation:
            if not parsed:
                board = GameBoardCls(board_string=kwargs.pop("board_string"), game_type=kwargs.pop("game_type"))
        else:
            board = GameBoardCls(board_string="START", game_type=self.config.game_type)

        self._game_board = board
        self._game_ai.reset_caches()

        game_str = self._game_board.to_game_string()
        print(game_str)
        return game_str

    def check_board(self, check_game_over=True):
        if self._game_board is None:
            raise NoBoardException
        if check_game_over:
            if self._game_board.game_is_over:
                raise GameIsOverException

    def play(self, move_string):
        self.check_board()

        try:
            move = NotationUtils.parse_move_string(self._game_board, move_string)
        except ValueError or Exception:
            raise ValueError("Unable to parse '%s'." % move_string)

        _, move_string = NotationUtils.try_normalize_boardspace_move_string(move_string)
        self._game_board.play(move, move_string)

        game_str = self._game_board.to_game_string()
        print(game_str)
        return game_str

    def pass_turn(self):
        self.check_board()
        self._game_board.pass_turn()
        print(self._game_board.to_game_string())

    def valid_moves(self):
        self.check_board()
        valid_moves = self._game_board.get_valid_moves()
        print(NotationUtils.to_boardspace_move_string_list(self._game_board, valid_moves))
        return self._game_board.to_game_string()

    def best_move(self, **kwargs):
        self.check_board()

        if 'max_time' not in kwargs and 'max_depth' not in kwargs:
            raise ValueError("You must specify either a max_depth or a max_time!")
        if 'max_time' in kwargs:
            kwargs['max_time'] = datetime.timedelta(seconds=int(kwargs.get('max_time')))

        self._async_queue = TaskQueue()
        self._async_queue.enqueue(self._game_ai.get_best_move_async, self._game_board, **kwargs)

        results = self.StartAsyncCommand.on_change.fire()
        if isinstance(results, list) and len(results[0]) > 0:
            best_move = results[0][0]
        else:
            best_move = None

        if best_move is None:
            raise ValueError("Null move returned!")
        elif not isinstance(best_move, Move):
            raise ValueError(best_move)

        print(NotationUtils.to_boardspace_move_string(self._game_board, best_move))
        return best_move

    def undo(self, moves=1):
        self.check_board(check_game_over=False)

        if moves < 1 or moves > self._game_board.board_history_count:
            raise UndoInvalidNumberOfMovesException(moves)

        for i in range(moves):
            self._game_board.undo_last_move()

        print(self._game_board.to_game_string())

    def options_list(self):
        self.options_get("max_branching_factor")
        self.options_get("max_helper_threads")
        self.options_get("ponder_during_idle")
        self.options_get("transposition_table_size_mb")
        self.options_get("report_intermediate_best_moves")
        self.options_get("game_type")

    # noinspection PyMethodMayBeStatic
    def options_get(self, opt_key):
        if opt_key is None or opt_key.isspace():
            raise ValueError("opt_key is None or whitespace")
        opt_key = opt_key.strip()

        try:
            opt_type, value, values = eval(opt_key_dict[opt_key])
        except KeyError:
            print("The option \"%s\" is not valid." % opt_key)
            return

        if values is None or values.isspace():
            print("%s;%s;%s" % (opt_key, opt_type, value))
        else:
            print("%s;%s;%s;%s" % (opt_key, opt_type, value, values))

    def options_set(self, opt_key, value):
        if opt_key is None or opt_key.isspace():
            raise ValueError("opt_key is None or whitespace")
        opt_key = opt_key.strip()

        refresh_ai = False

        if opt_key == "max_branching_factor":
            self.config.parse_max_branching_factor_value(value)
            refresh_ai = True
        elif opt_key == "max_helper_threads":
            self.config.parse_max_helper_threads_value(value)
        elif opt_key == "ponder_during_idle":
            self.config.parse_ponder_during_idle_value(value)
        elif opt_key == "transposition_table_size_mb":
            self.config.parse_transposition_table_size_mb_value(value)
            refresh_ai = True
        elif opt_key == "report_intermediate_best_moves":
            self.config.parse_report_intermediate_best_moves_value(value)
            refresh_ai = True
        elif opt_key == "game_type":
            self.config = GameEngineConfig.get_default_config("Extended")
            self.config.parse_game_type_value(value)
            refresh_ai = True
        else:
            print("The option \"%s\" is not valid." % opt_key)

        self.options_get(opt_key)

        if refresh_ai:
            self.init_ai()

    """
    def start_ponder(self):
        if self.config.ponder_during_idle != "Disabled" and not self._is_pondering and \
                self._game_board is not None and self._game_board.game_in_progress:

            if self.config.report_intermediate_best_moves:
                self._game_ai.best_move_found.on_change -= self.on_best_move_found

            self._ponder_queue = TaskQueue()

            max_threads = self.config.max_helper_threads if self.config.ponder_during_idle == "MultiThreaded" else 0
            kwargs = {
                'max_helper_threads': max_threads,
            }
            ponder_board = deepcopy(self._game_board)
            self._ponder_queue.enqueue(self._game_ai.get_best_move_async, ponder_board, **kwargs)

            global loop
            loop.run_in_executor(None, self._ponder_queue.run, loop)
            self._is_pondering = True

    def stop_ponder(self):
        if self._is_pondering:
            global loop
            loop.run_in_executor(None, self._ponder_queue.stop)

            self._is_pondering = False

            if self.config.report_intermediate_best_moves:
                self._game_ai.best_move_found.on_change += self.on_best_move_found
    """

    def on_start_async_command(self):
        return self._async_queue.run()

    def on_end_async_command(self):
        self._async_queue.stop()

    def exit(self):
        self._game_board = None
        self.exit_requested = True


opt_key_dict = {
    "max_branching_factor": "self.config.get_max_branching_factor_value()",
    "max_helper_threads": "self.config.get_max_helper_threads_value()",
    "ponder_during_idle": "self.config.get_ponder_during_idle_value()",
    "transposition_table_size_mb": "self.config.get_transposition_table_size_mb_value()",
    "report_intermediate_best_moves": "self.config.get_report_intermediate_best_moves_value()",
    "game_type": "self.config.get_game_type_value()",
}


class CommandException(Exception):
    def __init__(self, message=None):
        if message:
            raise ValueError(message)
        else:
            raise ValueError("Invalid command. Try 'help' to see a list of valid commands.")


class NoBoardException(CommandException):
    def __init__(self):
        super().__init__("No game in progress. Try 'newgame' to start a new game.")


class GameIsOverException(CommandException):
    def __init__(self,):
        super().__init__("The game is over. Try 'newgame' to start a new game.")


class UndoInvalidNumberOfMovesException(CommandException):
    def __init__(self, moves):
        message = "Unable to undo %s moves." % moves
        super().__init__(message)
