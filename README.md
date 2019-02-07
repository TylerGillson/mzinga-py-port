# mzinga-py-port

- [Overview](#overview)
- [What's New](#whats-new)
- [Usage](#usage)
- [Limitations](#limitations)

## Overview
mzinga-py-port is a Python implementation and extension of Jon Thysell's [Mzinga](https://github.com/jonthysell/Mzinga) system, which was written in C#. My attempts at improving Mzinga are being conducted as an Honours undergraduate research project in AI.

## What's New?
The extended Mzinga system allows full backwards compatibility with the original system, while introducing
the option to play against an "extended AI".

### Metrics
The extended AI computes a variety of additional piece metrics when evaluating
board positions. These include:
1. Re-defined “Quiet” moves to exclude moves which unpin enemy bugs
2. Re-defined “Noisy” moves to include moves which pin enemy bugs into a space adjacent to their Queen Bee
3. Added metrics for whether or not a piece has an available move which would create various types of “rings”:
   * Defense rings - defense rings are formations which create a non-sliding-queen-space adjacent to your Queen Bee
   * Noisy rings - noisiness is determined according to the ratio of freed friendly versus unfriendly bugs; or, more crucially, whether the ring frees a Queen Bee. A ring which frees more friendly bugs than enemy bugs is considered "noisy".

The extended AI also considers several new board-level metrics:
1. A NumNonSlidingQueenSpaces metric to quantify the number of spaces adjacent to each Queen Bee that must either be jumped into by a Grasshopper or dropped into by a Beetle
2. A NoisyRing metric to indicate whether or not the current board configuration already contains noisy rings of either colour; and if so, how many
3. A QueenLife metric to indicate the proximity of each player to defeat (the number of a Queen's adjacent spaces which are unoccupied)

### Genetic Algorithm (Trainer module)
The extended system uses different genetic operators when breeding Extended AI profiles - while maintaining the original functionality for Original AI profiles. The original mating functionality computed a weighted average between the two parents +/- a random fuzzy factor for each metric weight of the child profile. The extended system performs a cross-over operation followed by a mutate operation.

#### Cross-over
A random index into an arbitrary metric weight vector is selected. The child then receives a new metric weight vector composed of the "left" portion of parent A's vector, concatenated with the "right" portion of parent B's vector.

#### Mutate
A random index into the child's metric weight vector is selected. The metric weight at said index is then randomly modulated either up or down by a value selected at random from {1, ..., 10}.

## Usage
There are two primary executables: MzingaEngine/Program.py and MzingaTrainer/Program.py, which launch the game engine and the trainer (metric weight optimization module), respectively.

### Game Engine
The game engine is used to play against the default AI, whose configuration file is: MzingaShared/Engine/GameEngineConfig.py. To play, ensure that your PYTHONPATH is configured correctly, then execute: ```python3 Program.py```. Once the game engine has loaded, type ```help``` to see a summary of all the game engine commands. See also: [Jon Thysell's Game Engine Documentation](https://github.com/jonthysell/Mzinga/wiki/UniversalHiveProtocol#engine-commands).

### Trainer
The trainer executes an evolutionary algorithm to obtain optimized metric weights for the default game engine's AI. It has many configuration options, which can be reviewed in: MzingaTrainer/Program.py. The RunConfigurations folder contains a directory of PyCharm run configurations which are a good place to start. 

Primary Functionalities:
1. Battle - compete two AI profiles against each other 1 or more times consecutively.
2. Battle Royale - have each AI profile in a group of AI profiles compete against every other AI once.
3. Cull - eliminate a specific number of AI profiles from a group having the lowest ELO scores.
4. Enumerate - list each AI profile (name + wins/losses/draws) in a directory in order of ELO score.
5. Analyze - generate a .csv file containing all the data for the AI profiles in a directory.
6. Generate - generate a specific number of AI profiles with random metric weights (Original or Extended).
7. Lifecycle - iteratively compete (via Battle Royale or Tournament), breed, then cull a pool of AI profiles for a specific number of generations. This is the "evolutionary algorithm" which can be used to obtain optimized metric weights.
8. Mate - pair off and mate the AI profiles in a directory (pair randomly or based on ELO score).
9. Tournament - pair off the AI profiles in a directory and have them execute a round-robin tournament.

Each of the latter functionalities can be configured in a variety of ways. Please refer to the run configurations, as well as MzingaTrainer/Program.py, MzingaTrainer/Trainer.py, and MzingaTrainer/TrainerSettings.py for a deeper understanding of their possible usage.

## Limitations
For the sake of expediency, my Python implementation lacks support for any of Hive's expansion pieces.
Additionally, my implementation does not "ponder" in between human moves; nor does it utilize Lazy SMP
helper threads for accelerating the AI's search procedure.
