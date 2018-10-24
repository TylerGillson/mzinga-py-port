import sys

from HiveOnline.MzingaShared.Engine import GameEngineConfig
from HiveOnline.MzingaShared.Engine.GameEngine import GameEngine
from HiveOnline.MzingaShared.Engine.GameEngineConfig import GameEngineConfig as GameEngineConfigCls


class Program:
    ID = "Mzinga.Engine v.1"
    _intercept_cancel = False
    engine = None

    def main(self, args):
        valid_args = args is not None and len(args) > 0
        config = self.load_config(args[0]) if valid_args else GameEngineConfig.get_default_config()
        self.engine = GameEngine(self.ID, config)
        self.engine.parse_command("info")

        try:
            while not self.engine.exit_requested:
                command = input()
                if command and not command.isspace():
                    self.engine.parse_command(command)
        except KeyboardInterrupt:
            print("Exiting...")

    @staticmethod
    def load_config(path):
        if path is None or path == '':
            raise ValueError("path is None or an empty string")

        f = open(path, '+wb')
        return GameEngineConfigCls(f)


if __name__ == '__main__':
    Program().main(sys.argv[1:])
