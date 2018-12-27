# Starcraft-2-Trainer

A trainer app for Starcraft 2. Import your replay, and sc2trainer will rate you on how good your macro abilities were.

## Scoring

The program yields a score between 0-100000 which incorporates how well you followed your build order of choice, how often you were supply capped, and how often you were hoarding resources.

## Additional output

The program can also be tweaked to let you know at what timestamp your macro was off, and what you can improve. See the commented print statements in the source.

## Dependencies

To run Starcraft-2-Trainer, you must have python3 installed on your system. The program also requires the followind packages:
- sc2reader library by https://github.com/GraylinKim/:

```pip3 install sc2reader```
-  the matplotlib library and all its dependencies:

```pip3 install matplotlib```
- the python3 tkinter library for gui and plotting:

```sudo apt-get install python3-tk```

