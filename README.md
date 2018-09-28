# Reddit Bots

A collection of miscellaneous Reddit bots.

## nba_tweets

Posts tweets by certain NBA reporters to r/nba

## statbot

Uses my nba_scrape library to provide NBA stats when requested by the trigger
!STAT on r/nba.

### Usage:

`!STAT player_name stat1/stat2/etc. [YYYY-YY] [-flag]`

#### Support for the following stats:

Team, Games Played (GP), Minutes (MIN), Points (PTS), Field Goal Attempts (FGA),
Field Goals Made (FGM), Field Goal Percentage (FG%), Three Point Attempts (3PA),
Three Pointers Made (3PM), Three Point Percentage (3P%), Free Throw Attempts (FTA),
Free Throws Made (FTM), Free Throw Percentage (FT%), Offensive Rebounds (OREB),
Defensive Rebounds (DREB), Rebounds (REB), Assists (AST), Steals (STL), Blocks (BLK),
Turnovers (TOV), Personal Fouls (PF), and True Shooting Percentage (TS%).

#### YYYY-YY:

This argument is optional. Without it, the bot returns stats from all seasons,
including career averages. This argument could also be "career" (case-insensitive)
to return only overall averages.

#### Flags:

This argument is also optional. By default, the bot returns regular season stats.
Adding "-p" or "-playoffs" will return only playoffs stats, while "-b" or "-both"
will return both.

#### Example:

`!STAT LeBron James pts/fga/fg%`

#### Notes:

The bot is case insensitive.
The order of the parameters does not matter.
TS% is calculated using FGA, FTA, and PTS; due to rounding errors, there may be minor inaccuracies.
