# Ava's Global speedrunning leaderboard
A global leaderboard for competitive speedrunning powered by speedrun.com

Disclaimer: This is still in early testing and subject to drastic changes if needed.  
Ex.: I'm planning of making this an actual webap with its own SQL database rather than a client connecting to GSheets.


**[See the leaderboard](https://docs.google.com/spreadsheets/d/1KpMnCdzFHmfU0XDzUon5XviRis1MvlB5M6Y8fyIvcmo#gid=518408346)**  
**[DOWNLOAD THE CLIENT](https://github.com/Avasam/speedrun.com_-unofficial-_global_leaderboard/releases)**  
You can download this compiled version of the client to update any user you want.


How the score is calculated:
- The sum of every valid PB of a user is scored according to a formula. (see [Formula/Curves](https://docs.google.com/spreadsheets/d/1Wv63zu3YY7vAJAzWgZwL4rHE9esxxN0B8DztJgNyjiQ#gid=156937478))
- Said formula gives you more points the closest to #1 you are on a leaderboard and the more players there are. Wich encourages having a good rank in games with a lot of players without having to be first (altough being in the top does give a lot of points because you have a lot more competition).
- The only 2 arbritrary numbers are: 4 and 60%
    - 4 is the minimum amount of players that should be present in a leaderboard.
    - 60% minimum percentile needed in a leaderboard for a run to be worth any point.
- Runs w/o video/image verifications are not considered AND not counted.
- Leaderboards based on score rather than speed are excluded†



†The method used to differentiate speedruns from scores leaderboards can very rarely give false-negative. It happens when only the 1st place is/are are using the primary time comparison ([see this example screenshot](http://puu.sh/xfrpr/57d6358440.jpg)) wich you can easily fix if you're a mod or if your run is part of the leaderboard by updating the times.
