pyi-makespec ^
    --onefile ^
    --name "speedrun.com (unofficial) global leaderboard" ^
    --icon icon.ico ^
    --add-binary icon.ico;. ^
    --add-binary LICENSE.txt;. ^
    --add-binary README.md;. ^
    --add-binary "C:\ProgramData\speedrun.com (unofficial) global leaderboard";. ^
    ui.py
    ::--key KEY
    ::--version-file FILE

pyinstaller ^
    --distpath ..\ ^
    --noconfirm ^
    --clean ^
    --onefile ^
    "speedrun.com (unofficial) global leaderboard.spec"
    ::--key KEY
    ::--version-file FILE

pyi-makespec ^
    --onefile ^
    --name "speedrun.com (unofficial) global leaderboard [noconsole]" ^
    --icon icon.ico ^
    --add-binary icon.ico;. ^
    --add-binary LICENSE.txt;. ^
    --add-binary README.md;. ^
    --add-binary "C:\ProgramData\speedrun.com (unofficial) global leaderboard";. ^
    --noconsole ^
    ui.py
    ::--key KEY
    ::--version-file FILE

pyinstaller ^
    --distpath ..\ ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --noconsole ^
    --name "speedrun.com (unofficial) global leaderboard [noconsole]" ^
    "speedrun.com (unofficial) global leaderboard [noconsole].spec"
    ::--key KEY
    ::--version-file FILE

PAUSE