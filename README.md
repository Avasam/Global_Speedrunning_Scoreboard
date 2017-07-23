# speedrun.com_-unofficial-_global_leaderboard
A global leaderboard for competitive speedrunning

Disclaimer: This is still in early testing and subject to drastic changes if needed.  
Ex.: I may plan on making my own SQL database instead of using a Google Sheet or making the client a webservice.


**See the leaderboard**: https://docs.google.com/spreadsheets/d/1KpMnCdzFHmfU0XDzUon5XviRis1MvlB5M6Y8fyIvcmo#gid=518408346
**DOWNLOAD THE CLIENT**: https://github.com/Avasam/speedrun.com_-unofficial-_global_leaderboard/releases  
You can download this compiled version of the client to update any user you want.


How the score is calculated:
- The sum of every valid PB of a user is scored according to a formula. (see https://docs.google.com/spreadsheets/d/1KpMnCdzFHmfU0XDzUon5XviRis1MvlB5M6Y8fyIvcmo#gid=1762022442)
- Said formula gives you more points the closest to #1 you are on a leaderboard and the more players there are. Wich encourages having a good rank in games with a lot of players without having to be first (altough being in the top does give a lot of points because you have a lot more competition).
- It uses exponential decay and a natural logaritmic function. The only 2 arbritrary numbers are: 4 and K
- 4 is the minimum amount of players that should be present in a leaderboard. K is just the exponential decay constant (I balance it to be the highest number to give a score of 1 when you're 20th/30)
- Said score also can't be more than leaderboard size minus your run's rank

Individual levels are not considered atm (only full game runs).

Runs w/o video/image verifications are not considered AND not counted.

If there's any balance issue in the formulas, that's an easy fix. (ex. I might change the minimum amount of players needed in a leaderboard or adjust the rate of decay, but that's literally just changing a constant, I'm not too worried about it right now).
