import datetime
# import asyncio
# from copy import deepcopy

from MzingaShared.Core.Board import InvalidMoveException
from MzingaShared.Core.BoardHistory import BoardHistory
from MzingaShared.Core.GameBoard import GameBoard
from MzingaShared.Core.Move import Move
from Utils.Events import Broadcaster
from Utils.TaskQueue import TaskQueue

debug = False
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
        "board": "self.board() if param_count == 0 else self.board(split[1])",
        "play": "self.raise_command_exception() if param_count < 1 else self.play(split[1])",
        "pass": "self.pass_turn()",
        "validmoves": "self.valid_moves()",
        "undo": "self.undo() if param_count == 0 else self.undo(split[1])",
        "history": "self.history()",
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

        if self.config.ReportIntermediateBestMoves:
            self._game_ai.BestMoveFound.on_change += self.on_best_move_found

    @staticmethod
    def on_best_move_found(args):
        if args is None:
            raise ValueError("args is None")
        if args.Move is None:
            raise ValueError("Null move reported!")

        print("Current BMF (move/depth/score): %s;%d;%2f" % (args.Move, args.Depth, args.Score))

    def parse_command(self, command):
        if command is None or command.isspace():
            raise ValueError("command is None")

        command = command.replace('\t', ' ')
        split = list(filter(None, command.split()))
        err = False

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
            else:
                return eval(self.cmd_dict[cmd])

        except KeyError:
            print("Invalid command")
            err = True
        except InvalidMoveException as ex:
            print("invalidmove %s", ex.message)
            err = True
        except Exception as ex:
            print("err %s" % ex)
            err = True

        if not err:
            print("ok")
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
        print("history")
        print("options")
        print("exit")

    def board(self, board_string=None):
        if debug:
            if not (board_string is None or board_string.isspace()):
                self._game_board = GameBoard(board_string)
                self._game_ai.reset_caches()
        if self._game_board is None:
            raise NoBoardException
        print(self._game_board)

    def new_game(self, **kwargs):
        self._game_board = GameBoard("START") if not kwargs else GameBoard(kwargs.pop("board_string"))
        self._game_ai.reset_caches()
        print(self._game_board)
        return str(self._game_board)

    def check_board(self, check_game_over=True):
        if self._game_board is None:
            raise NoBoardException
        if check_game_over:
            if self._game_board.game_is_over:
                raise GameIsOverException

    def play(self, move_string):
        self.check_board()
        self._game_board.play(Move(move_string=move_string))
        print(self._game_board)
        return str(self._game_board)

    def pass_turn(self):
        self.check_board()
        self._game_board.pass_turn()
        print(self._game_board)

    def valid_moves(self):
        self.check_board()
        valid_moves = self._game_board.get_valid_moves()
        print(valid_moves)
        return str(self._game_board)

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

        print(best_move)
        return best_move

    def undo(self, moves=1):
        self.check_board(check_game_over=False)

        if moves < 1 or moves > self._game_board.board_history_count:
            raise UndoInvalidNumberOfMovesException(moves)

        for i in range(moves):
            self._game_board.undo_last_move()
        print(self._game_board)

    def history(self):
        self.check_board(check_game_over=False)
        history = BoardHistory(board_history=self._game_board.board_history)
        print(history)

    def options_list(self):
        self.options_get("MaxBranchingFactor")
        self.options_get("MaxHelperThreads")
        self.options_get("PonderDuringIdle")
        self.options_get("TranspositionTableSizeMB")
        self.options_get("ReportIntermediateBestMoves")

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

        if opt_key == "MaxBranchingFactor":
            self.config.parse_max_branching_factor_value(value)
            refresh_ai = True
        elif opt_key == "MaxHelperThreads":
            self.config.parse_max_helper_threads_value(value)
        elif opt_key == "PonderDuringIdle":
            self.config.parse_ponder_during_idle_value(value)
        elif opt_key == "TranspositionTableSizeMB":
            self.config.parse_transposition_table_size_mb_value(value)
            refresh_ai = True
        elif opt_key == "ReportIntermediateBestMoves":
            self.config.parse_report_intermediate_best_moves_value(value)
            refresh_ai = True
        else:
            print("The option \"%s\" is not valid." % opt_key)

        self.options_get(opt_key)

        if refresh_ai:
            self.init_ai()

    """
    def start_ponder(self):
        if self.config.PonderDuringIdle != "Disabled" and not self._is_pondering and \
                self._game_board is not None and self._game_board.game_in_progress:

            if self.config.ReportIntermediateBestMoves:
                self._game_ai.BestMoveFound.on_change -= self.on_best_move_found

            self._ponder_queue = TaskQueue()

            max_threads = self.config.MaxHelperThreads if self.config.PonderDuringIdle == "MultiThreaded" else 0
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

            if self.config.ReportIntermediateBestMoves:
                self._game_ai.BestMoveFound.on_change += self.on_best_move_found
    """

    def on_start_async_command(self):
        return self._async_queue.run()

    def on_end_async_command(self):
        self._async_queue.stop()

    def exit(self):
        self._game_board = None
        self.exit_requested = True


opt_key_dict = {
    "MaxBranchingFactor": "self.config.get_max_branching_factor_value()",
    "MaxHelperThreads": "self.config.get_max_helper_threads_value()",
    "PonderDuringIdle": "self.config.get_ponder_during_idle_value()",
    "TranspositionTableSizeMB": "self.config.get_transposition_table_size_mb_value()",
    "ReportIntermediateBestMoves": "self.config.get_report_intermediate_best_moves_value()",
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
