# mzinga-py-port

## Overview
mzinga-py-port is a Python implementation and extension of Jon Thysell's Mzinga system, which was written in C#. [See Mzinga.](https://github.com/jonthysell/Mzinga)
My attempts at improving Mzinga are being conducted as an Honours undergraduate research project in AI.

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

## Limitations
For the sake of expediency, my Python implementation lacks support for any of Hive's expansion pieces.
Additionally, my implementation does not "ponder" in between human moves; nor does it utilize Lazy SMP
helper threads for accelerating the AI's search procedure.
