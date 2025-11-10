yt.py
=====

How use:
--------
Really not optimised for others to use. But you can give it a try.
 - setup virtual environment as per "requirements.txt"
 - rename the music table "data/test-table.csv" to "data/music_table.csv" to
 start out somewhere. You can personalize it later.
 - run `yt.py`
 - you copy and paste a yt url into the command line, the program should
 download, play and add it to your library. For playlists the same, plus a new
 playlist with the same name will be created.

Example Bat file:
```

```

Commands to use in the program:
  - ser :: search for song
  - del :: delete a song
  - correct title :: remove unusual characters from title
  - rename title :: rename title
  - tab :: print the list of songs
  - date :: print songs arranged by date, descending
  - freq :: print songs arranged by popularity, descending
  - re-freq :: print songs arranged by popularity, ascending
  - playlist :: show playlist actions
  - r :: replay a song
  - single :: play a url without adding it to the library
  - redownload :: force redownload of a song
  - random :: play a random song. Use '--force' to play it automatically
  - shuffle :: shuffles all the songs into one playlist, plays it
  - by_date :: play the songs by date of addition to the list
  - `,` :: playlist of song numbers divided by a comma, eg `12, 3, 8`
  - autist :: play the same song over and over again
  - help :: prints this list  

While the media is playing:
- use the keys displayed for the desired effect
- use number keys 0, 1, 2, ... 9 to skip to the 0, 10, 20,..., 90 % marks