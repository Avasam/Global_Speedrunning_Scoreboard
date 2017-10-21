# Ava's Global Speedrunning Scoreboard
A global scoreboard for competitive speedrunning powered by speedrun.com

Disclaimer: This is in constant testing and subject to changes if needed.

**[See the leaderboard](https://docs.google.com/spreadsheets/d/1KpMnCdzFHmfU0XDzUon5XviRis1MvlB5M6Y8fyIvcmo)**  
**[DOWNLOAD THE CLIENT](https://github.com/Avasam/speedrun.com_-unofficial-_global_leaderboard/releases)** You can download this compiled version of the client to update any user you want.

How the score is calculated using a relative time comparison system:
- Leaderboards based on score rather than speed are excluded.†
- Runs without video/image verifications are not considered AND not counted.
- The last 5% (that's 1/20 runs) of every leaderboard is ignored to help getting rid of extreme outliers.
- Maths:
  - The population (leaderboard size), mean and standard deviation is calculated.
  - The last run is forced to be worth 0 points by adding its deviation to the signed (±) deviation from the mean and standard deviation of the leaderboard making: `adjusted_deviation/adjusted_standard_deviation=0`.
  - The deviation is then normalized so that the last run is still worth 0, but the mean is worth exactly 1.
  - A certainty adjustment is applied just to help avoiding runs being worth an absurd amount of points just because there's only 1/4 people who actually ran fast.  
  Formula is as follows: `certainty_adjustment = 1-1/original_population` meaning a leaderboard that originally had before the 5% cutoff :
    - 3 runs = 66%††
    - 4 runs = 75%
    - 5 runs = 80%
    - [...]
    - 20 runs = 95%
    - etc.
  - The current linear function (0 at the worst time and 1 around the mean) is made into a square function without changing those two points simply by squaring the numbers.  
  Meaning that bad runs are increasingly worth less and good runs are increasingly worth more. In other words, this reflects the fact that getting a better time in a speedrun is increasingly harder, and so it is worth increasingly more.
  - A small time bonus is applied based on the current World Record (+100% for every 6h, a 40m run would give +0.1). This isn't much, but makes really long runs still worth it without punishing smaller runs. Longer runs also mean you get to practice the entire game a lot less and are more prone to mistakes.
- Individual Levels are considered, however their value is divided according to the amount of ILs in the same category.


†The method used to differentiate speedruns from scores leaderboards can very rarely give false-negative.  
It happens when only the 1st place is/are using the primary time comparison ([see this example screenshot](http://puu.sh/xfrpr/57d6358440.jpg))
which you can easily fix if you're a mod or if your run is part of the leaderboard by updating the times.  
††You might notice 1 and 2 are missing. That's because 95% of 2 rounded down is 1 and the last run (in this case the only run) is always worth 0.

Special thanks to [Dugongue](http://www.speedrun.com/user/Dugongue) for testing a lot.  
The [icon](favicon.ico) is based off [speedrun.com's logo](https://www.speedrun.com/about).
