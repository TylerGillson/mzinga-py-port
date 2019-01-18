import sys
import datetime

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

                cmd = self.parse_arguments(args, t.trainer_settings)
                cmd_dict[cmd]()

        except KeyError:
            self.show_help()
        except Exception as ex:
            print("Error: %s" % ex)
        finally:
            return

    @staticmethod
    def show_help():
        print("Usage:")
        print("Mzinga.Trainer.py [command] ([parametername] [parametervalue]...)\n")

        print("Example:")
        print("Mzinga.Trainer.py enumerate -ProfilePath /Users/<username>/<path_to_profiles>/\n")

        print("Commands:")

        print("battle                 Fight a single battle between two profiles")      # Tested
        print("battleroyale           Fight every profile against each other")          # Tested
        print("cull                   Delete the lowest ranking profiles")              # Tested
        print("enumerate              List all of the profiles")                        # Tested
        print("analyze                Analyze all of the profiles")                     # Tested
        print("generate               Create new random profiles")                      # Tested
        print("lifecycle              Battle, cull, mate cycle for profiles")           # Tested
        print("mate                   Mate every profile with each other")              # Tested
        print("tournament             Fight a single elimination tournament")           # Tested
        print()

        print("Parameters:")

        print("-GameType                Original or Extended AI")
        print("-MixedGameTypes          Whether original & extended AIs will be competing")
        print("-LogToFile               Whether output is piped to a file or the console")
        print("-ProfilePath             Where the profiles are stored")
        print("-WhiteProfilePath        The white profile in a single battle")
        print("-BlackProfilePath        The black profile in a single battle")
        print("-CullKeepCount           How many to profiles to keep when culling")
        print("-GenerateCount           How many profiles to generate")
        print("-GenerateMinWeight       The minimum weight value for random profiles")
        print("-GenerateMaxWeight       The maximum weight value for random profiles")
        print("-LifecycleGenerations    The number of generations to run")
        print("-LifecycleBattles        The number/type of battles in each generation.")
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

    @staticmethod
    def parse_args(arg, args, i, trainer_settings):
        if arg in ["gt", "gametype"]:
            trainer_settings.game_type = args[i + 1]
        elif arg in ["mgt", "mixedgametypes"]:
            trainer_settings.mixed_game_types = args[i + 1] == "True"
        elif arg in ["ltf", "logtofile"]:
            trainer_settings.log_to_file = args[i + 1] == "True"
        elif arg in ["pp", "profilepath"]:
            trainer_settings.profile_path = args[i + 1]
        elif arg in ["wpp", "whiteprofilepath"]:
            trainer_settings.white_profile_path = args[i + 1]
        elif arg in ["bpp", "blackprofilepath"]:
            trainer_settings.black_profile_path = args[i + 1]
        elif arg in ["ckc", "cullkeepcount"]:
            trainer_settings.cull_keep_count = int(args[i + 1])
        elif arg in ["gc", "generatecount"]:
            trainer_settings.generate_count = int(args[i + 1])
        elif arg in ["gminw", "generateminweight"]:
            trainer_settings.generate_min_weight = float(args[i + 1])
        elif arg in ["gmaxw", "generatemaxweight"]:
            trainer_settings.generate_max_weight = float(args[i + 1])
        elif arg in ["lg", "lifecyclegenerations"]:
            trainer_settings.lifecycle_generations = int(args[i + 1])
        elif arg in ["lb", "lifecyclebattles"]:
            trainer_settings.lifecycle_battles = int(args[i + 1])
        elif arg in ["mb", "maxbattles"]:
            trainer_settings.max_battles = int(args[i + 1])
        elif arg in ["mcb", "maxconcurrentbattles"]:
            trainer_settings.max_concurrent_battles = int(args[i + 1])
        elif arg in ["bsp", "battleshuffleprofiles"]:
            trainer_settings.battle_shuffle_profiles = args[i + 1] == "True"
        elif arg in ["mdraws", "maxdraws"]:
            trainer_settings.max_draws = int(args[i + 1])
        elif arg in ["bbtl", "bulkbattletimelimit"]:
            trainer_settings.bulk_battle_time_limit = int(args[i + 1])
        elif arg in ["pr", "provisionalrules"]:
            trainer_settings.provisional_rules = args[i + 1] == "True"
        elif arg in ["pgc", "provisionalgamecount"]:
            trainer_settings.provisional_game_count = int(args[i + 1])
        elif arg in ["mminm", "mateminmix"]:
            trainer_settings.mate_min_mix = float(args[i + 1])
        elif arg in ["mmaxm", "matemaxmix"]:
            trainer_settings.mate_max_mix = float(args[i + 1])
        elif arg in ["mpc", "mateparentcount"]:
            trainer_settings.mate_parent_count = int(args[i + 1])
        elif arg in ["msp", "mateshuffleparents"]:
            trainer_settings.mate_shuffle_parents = args[i + 1] == "True"
        elif arg in ["tts", "transtablesize"]:
            trainer_settings.trans_table_size = int(args[i + 1])
        elif arg in ["mdepth", "maxdepth"]:
            trainer_settings.max_depth = int(args[i + 1])
        elif arg in ["tmt", "turnmaxtime"]:
            trainer_settings.turn_max_time = datetime.timedelta(seconds=int(args[i + 1]))
        elif arg in ["btl", "battletimelimit"]:
            trainer_settings.battle_time_limit = int(args[i + 1])
        elif arg in ["tpp", "targetprofilepath"]:
            trainer_settings.target_profile_path = args[i + 1]
        elif arg in ["mht", "maxhelperthreads"]:
            trainer_settings.max_helper_threads = int(args[i + 1])

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

            try:
                self.parse_args(arg, args, i, trainer_settings)
                i += 2
            except KeyError:
                raise Exception("Unknown parameter: %s" % args[i])

        return cmd


if __name__ == '__main__':
    Program().main(sys.argv[1:])
