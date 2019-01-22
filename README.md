# mzinga-py-port

## Overview
mzinga-py-port is a Python implementation and extension of Jon Thysell's Mzinga system - written in C#. [See Mzinga.](https://github.com/jonthysell/Mzinga)
My attempts at improving Mzinga were undertaken as an Honours undergraduate research project in AI.

## What's New?
The extended Mzinga system allows full backwards compatibility with the original system, while introducing
the option to play against an "extended AI". The extended AI computes 5 additional metrics when evaluating
board positions. These include:
1. Re-defined “Quiet” moves to exclude moves which unpin enemy bugs
2. Re-defined “Noisy” moves to include moves which pin enemy bugs into a space adjacent to their Queen Bee
3. Added a NumNonSlidingQueenSpaces metric to quantify the number of spaces adjacent to each Queen Bee that must either be jumped into by a Grasshopper or dropped into by a Beetle
4. Added metrics for whether or not the current board configuration contains various types of rings
    * Defense rings - 
    * Noisy rings - 
5. Added metrics for whether or not the piece has an available move which would create various types of “rings”. Ring desirability is classified according to the ratio of freed friendly versus unfriendly bugs; or, more crucially, whether the ring frees a Queen Bee.

## Limitations
For the sake of expediency, my Python implementation lacks support for any of Hive's expansion pieces.
Additionally, my implementation does not "ponder" in between human moves; nor does it utilize Lazy SMP
helper threads for accelerating the AI's search procedure.