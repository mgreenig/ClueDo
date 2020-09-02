# ClueDo

A bot that plays ClueDo. This bot controls a single player in the game and controls its own movements on the board.

## Table of contents

`Board_graph.py` -- contains the graph used to represent the ClueDo board 

`ClueDo.py` -- contains the class used to track game information

`PlayGame.py` -- script for starting the game; run from the command line to play

## Demo

The bot uses PyInquirer to interact with the user. When you start the game by running:

``` console
python PlayGame.py
```

You will receive the following prompt, asking a player to be selected:

``` console
? Which characters are playing?  (<up>, <down> to move, <space> to select, <a> to toggle, <i> to invert)
 ❯○ Rev Green
  ○ Dr Orchid
  ○ Colonel Mustard
  ○ Mrs Peacock
  ○ Miss Scarlett
  ○ Prof Plum
```

Then you will be asked to specify which of the players the bot is to play:

``` console 
? Which character will I be playing?  (Use arrow keys)
 ❯ Rev Green
   Colonel Mustard
   Miss Scarlett
```

And finally which cards the bot has been dealt.

``` console
? What are my cards?  (<up>, <down> to move, <space> to select, <a> to toggle, <i> to invert)
 ❯○ Rev Green
  ○ Dr Orchid
  ○ Revolver
  ○ Dagger
  ○ Candlestick
  ○ Ballroom
  ○ Hall
  ○ Miss Scarlett
  ○ Library
  ○ Conservatory
  ○ Wrench
  ○ Rope
  ○ Dining Room
  ○ Colonel Mustard
  ○ Lounge
  ○ Kitchen
  ○ Mrs Peacock
  ○ Lead Pipe
  ○ Prof Plum
  ○ Billiard Room
  ○ Study     
```

After selecting which player will go first, the game begins. On the bot's turn, the user will be prompted for a dice roll and asked whether any clue cards have been shown. Finally, at the end of the turn, if the bot has moved to a room, it will make a suggestion:

``` console
I have moved to the Library
Hm... what should I suggest...
I suggest Dr Orchid did it with the Rope in the Library
? If a player showed a card, please enter which one. If not, select None.  (Use arrow keys)
 ❯ Colonel Mustard
   Miss Scarlett
   None
```

On another player's turn, the bot will ask if the character has made a suggestion:

``` console
? Would Miss Scarlett like to make a suggestion?  (Use arrow keys)
 ❯ Yes
   No
```

And if so, will store information about the suggestion and the outcome:

