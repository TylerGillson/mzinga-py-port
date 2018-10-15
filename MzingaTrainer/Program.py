import sys
import os
from os.path import dirname
sys.path.append(dirname(os.getcwd()))  # Add root directory to PYTHONPATH

from MzingaTrainer.Trainer import Trainer


class Program:
    cmd_dict = None

    def main(self, args):
        try:
            print("Mzinga.Trainer v.1\n")

            if len(args) == 0:
                self.show_help()
            else:
                t = Trainer()
                cmd = self.parse_arguments(args, t.TrainerSettings)

                cmd_dict = {
                    "b": t.battle,
                    "battle": t.battle,
                    "br": t.battle_royale,
                    "battleroyale": t.battle_royale,
                    "c": t.cull,
                    "cull": t.cull,
                    "e": t.enumerate,
                    "enumerate": t.enumerate,
                    "a": t.analyze,
                    "analyze": t.analyze,
                    "g": t.generate,
                    "generate": t.generate,
                    "l": t.lifecycle,
                    "lifecycle": t.lifecycle,
                    "m": t.mate,
                    "mate": t.mate,
                    "t": t.tournament,
                    "tournament": t.tournament,
                }
                self.cmd_dict = cmd_dict
                cmd_dict[cmd]()

        except KeyError:
            self.show_help()
        except Exception as ex:
            print("Error: %s" % ex)

    @staticmethod
    def show_help():
        print("Usage:")
        print("Mzinga.Trainer.py [command] ([parametername] [parametervalue]...)\n")

        print("Example:")

        print("Mzinga.Trainer.py enumerate -ProfilesPath c:\\profiles\\\n")

        print("Commands:")
        print("battle                 Fight a single battle between two profiles")
        print("battleroyale           Fight every profile against each other")
        print("cull                   Delete the lowest ranking profiles")
        print("enumerate              List all of the profiles")
        print("analyze                Analyze all of the profiles")
        print("generate               Create new random profiles")
        print("lifecycle              Battle, cull, mate cycle for profiles")
        print("mate                   Mate every profile with each other")
        print("tournament             Fight a single elimination tournament")
        print()

        print("Parameters:")

        print("-ProfilesPath            Where the profiles are stored")
        print("-WhiteProfilePath        The white profile in a single battle")
        print("-BlackProfilePath        The black profile in a single battle")
        print("-CullKeepCount           How many to profiles to keep when culling")
        print("-GenerateCount           How many profiles to generate")
        print("-GenerateMinWeight       The minimum weight value for random profiles")
        print("-GenerateMaxWeight       The maximum weight value for random profiles")
        print("-LifecycleGenerations    The number of generations to run")
        print("-LifecycleBattles        The number/type of battles in each generation")
        print("-MaxBattles              The max number of battles in a battle royale")
        print("-MaxConcurrentBattles    The max number of battles at the same time")
        print("-BattleShuffleProfiles   Whether or not to have profiles fight in random order")
        print("-BulkBattleTimeLimit     The max time for tournaments / battle royales")
        print("-ProvisionalRules        Whether or not to use provisional rules")
        print("-ProvisionalGameCount    The number of games a profile stays provisional")
        print("-MaxDraws                The max number of times to retry battles that end in a draw")
        print("-MateMinMix              The min multiplier to mix up weights in children profiles")
        print("-MateMaxMix              The max multiplier to mix up weights in children profiles")
        print("-MateParentCount         The number of profiles to mate")
        print("-MateShuffleParents      Whether or not to have random parents mate")
        print("-TransTableSize          The maximum size of each AI's transposition table in MB")
        print("-MaxDepth                The maximum ply depth of the AI search")
        print("-TurnMaxTime             The maximum time to let the AI think on its turn")
        print("-BattleTimeLimit         The maximum time to let a battle run before declaring a draw")
        print("-TargetProfilePath       The target profile")
        print("-MaxHelperThreads        The maximum helper threads for each AI to use")
        print()

    def parse_arguments(self, args, trainer_settings):
        if args is None or len(args) == 0:
            raise ValueError("Invalid args")

        if trainer_settings is None:
            raise ValueError("Invalid trainer_settings.")

        cmd = args[0].lower()

        if cmd == "Unknown" or cmd not in self.cmd_dict.keys():
            raise Exception("Unknown command: %s" % args[0])

        i = 1
        while i < len(args):
            arg = args[i][1::].lower()

            global arg_dict
            try:
                exec(arg_dict[arg])
            except KeyError:
                raise Exception("Unknown parameter: %s" % args[i])

        return cmd


arg_dict = {
    "pp": "trainer_settings.ProfilesPath = args[i + 1])",
    "profilespath": "trainer_settings.ProfilesPath = args[i + 1]",

    "wpp": "trainer_settings.WhiteProfilePath = args[i + 1]",
    "whiteprofilepath": "trainer_settings.WhiteProfilePath = args[i + 1]",

    "bpp": "trainer_settings.BlackProfilePath = args[i + 1]",
    "blackprofilepath": "trainer_settings.BlackProfilePath = args[i + 1]",

    "ckc": "trainer_settings.CullKeepCount = int(args[i + 1])",
    "cullkeepcount": "trainer_settings.CullKeepCount = int(args[i + 1])",

    "gc": "trainer_settings.GenerateCount = int(args[i + 1])",
    "generatecount": "trainer_settings.GenerateCount = int(args[i + 1])",

    "gminw": "trainer_settings.GenerateMinWeight = float(args[i + 1])",
    "generateminweight": "trainer_settings.GenerateMinWeight = float(args[i + 1])",

    "gmaxw": "trainer_settings.GenerateMaxWeight = float(args[i + 1])",
    "generatemaxweight": "trainer_settings.GenerateMaxWeight = float(args[i + 1])",

    "lg": "trainer_settings.LifecycleGenerations = int(args[i + 1])",
    "lifecyclegenerations": "trainer_settings.LifecycleGenerations = int(args[i + 1])",

    "lb": "trainer_settings.LifecycleBattles = int(args[i + 1])",
    "lifecyclebattles": "trainer_settings.LifecycleBattles = int(args[i + 1])",

    "mb": "trainer_settings.MaxBattles = int(args[i + 1])",
    "maxbattles": "trainer_settings.MaxBattles = int(args[i + 1])",

    "mcb": "trainer_settings.MaxConcurrentBattles = int(args[i + 1])",
    "maxconcurrentbattles": "trainer_settings.MaxConcurrentBattles = int(args[i + 1])",

    "bsp": "trainer_settings.BattleShuffleProfiles = bool(args[i + 1])",
    "battleshuffleprofiles": "trainer_settings.BattleShuffleProfiles = bool(args[i + 1])",

    "mdraws": "trainer_settings.MaxDraws = int(args[i + 1])",
    "maxdraws": "trainer_settings.MaxDraws = int(args[i + 1])",

    "bbtl": "trainer_settings.BulkBattleTimeLimit = datetime.timedelta(args[i + 1])",
    "bulkbattletimelimit": "trainer_settings.BulkBattleTimeLimit = datetime.timedelta(args[i + 1])",

    "pr": "trainer_settings.ProvisionalRules = bool(args[i + 1])",
    "provisionalrules": "trainer_settings.ProvisionalRules = bool(args[i + 1])",

    "pgc": "trainer_settings.ProvisionalGameCount = int(args[i + 1])",
    "provisionalgamecount": "trainer_settings.ProvisionalGameCount = int(args[i + 1])",

    "mminm": "trainer_settings.MateMinMix = float(args[i + 1])",
    "mateminmix": "trainer_settings.MateMinMix = float(args[i + 1])",

    "mmaxm": "trainer_settings.MateMaxMix = float(args[i + 1])",
    "matemaxmix": "trainer_settings.MateMaxMix = float(args[i + 1])",

    "mpc": "trainer_settings.MateParentCount = int(args[i + 1])",
    "mateparentcount": "trainer_settings.MateParentCount = int(args[i + 1])",

    "msp": "trainer_settings.MateShuffleParents = bool(args[i + 1])",
    "mateshuffleparents": "trainer_settings.MateShuffleParents = bool(args[i + 1])",

    "tts": "trainer_settings.TransTableSize = int(args[i + 1])",
    "transtablesize": "trainer_settings.TransTableSize = int(args[i + 1])",

    "mdepth": "trainer_settings.MaxDepth = int(args[i + 1])",
    "maxdepth": "trainer_settings.MaxDepth = int(args[i + 1])",

    "tmt": "trainer_settings.TurnMaxTime = datetime.timedelta(args[i + 1])",
    "turnmaxtime": "trainer_settings.TurnMaxTime = datetime.timedelta(args[i + 1])",

    "btl": "trainer_settings.BattleTimeLimit = datetime.timedelta(args[i + 1])",
    "battletimelimit": "trainer_settings.BattleTimeLimit = datetime.timedelta(args[i + 1])",

    "tpp": "trainer_settings.TargetProfilePath = args[i + 1]",
    "targetprofilepath": "trainer_settings.TargetProfilePath = args[i + 1]",

    "mht": "trainer_settings.MaxHelperThreads = int(args[i + 1])",
    "maxhelperthreads": "trainer_settings.MaxHelperThreads = int(args[i + 1])",
}

if __name__ == '__main__':
    Program().main(sys.argv[1:])
