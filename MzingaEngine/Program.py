import sys
import os
from os.path import dirname
sys.path.append(dirname(os.getcwd()))  # Add root directory to PYTHONPATH

from Utils.Events import Broadcaster
from MzingaShared.Engine.GameEngine import GameEngine
from MzingaShared.Engine import GameEngineConfig
from MzingaShared.Engine.GameEngineConfig import GameEngineConfig as GameEngineConfigCls


class Program:
    ID = "Mzinga.Engine v.1"
    _intercept_cancel = False
    engine = None
    CancelKeyPress = Broadcaster()

    def main(self, args):
        valid_args = args is not None and len(args) > 0
        config = self.load_config(args[0]) if valid_args else GameEngineConfig.get_default_config()
        self.engine = GameEngine(self.ID, config)
        self.engine.parse_command("info")

        self.CancelKeyPress.on_change += self.console_cancel_key_press

        while not self.engine.exit_requested:
            command = input()
            if command and not command.isspace():
                self.engine.parse_command(command)

    def console_cancel_key_press(self):
        if self._intercept_cancel:
            self.engine.EndAsyncCommand.on_change.fire(self)

    @staticmethod
    def print_line(str_format, arg):
        print(str_format, arg)

    @staticmethod
    def load_config(path):
        if path is None or path == '':
            raise ValueError("path is None or an empty string")

        f = open(path, '+wb')
        return GameEngineConfigCls(f)


if __name__ == '__main__':
    Program().main(sys.argv[1:])
