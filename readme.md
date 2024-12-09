yt.py
=====

How use:
--------
Really not optimised for others to use. But you can give it a try.
 - rename the music table "data/test-table.csv" to "data/music_table.csv" to
 start out somewhere. You can personalize it later.
 - somehow make it happen, that you are able to run the `yt.py` script. That is
 the main one. Paths will be a problem I think. What works for me is to run the
 script with these batch commands:  
    `cd C:\<your path>\yt-player`  
    `C:\<path to the yt-player environment>\python.exe C:\<your path>\yt-player\yt.py`  

Commands to use in the program:
-------------------------------
you can input these commands to do stuff:
 - ser :: search for song title
 - del :: delete a song -- specify index
 - correct title :: remove unusual characters from title  -- specify index
 - tab :: print the list of songs
 - date :: print a list where the songs are arranged by date, latest at the bottom
 - r :: replay a song
 - single :: play a url without adding it to the library
 - help :: prints this list
 - random :: doesn't work, don't use