yt.py
=====

How use:
--------
Really not optimised for others to use. But you can give it a try.
 - setup virtual environment as per "requirements.txt"
 - rename the music table "data/test-table.csv" to "data/music_table.csv" to
 start out somewhere. You can personalize it later.
 - somehow make it happen, that you are able to run the `yt.py` script. That is
 the main one. What works for me is to run the script with these batch
 commands:  
    `cd C:\<your path>\yt-venv`  
    `C:\\Scripts\python.exe C:\<your path>\yt-venv\yt.py`  

Commands to use in the program:
-------------------------------
  - ser :: search for song
  - del :: delete a song
  - correct title :: remove unusual characters from title
  - rename title :: rename title
  - tab :: print the list of songs
  - date :: print songs arranged by date, descending
  - freq :: print songs arranged by popularity, descending
  - r :: replay a song
  - single :: play a url without adding it to the library
  - random :: play a random song. Use '--force' to play it automatically
  - shuffle :: shuffles all the songs into one playlist, plays it
  - by_date :: play the songs by date of addition to the list
  - `,` :: playlist of song numbers divided by a comma, eg `12, 3, 8`
  - autist :: play the same song over and over again
  - help :: prints this list