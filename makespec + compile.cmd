pyi-makespec ^
    --onefile ^
    --name "Global speedrunning leaderboard" ^
    --icon favicon.ico ^
    --add-binary favicon.ico;. ^
    --add-binary LICENSE.txt;. ^
    --add-binary README.md;. ^
    --add-binary "C:\ProgramData\Global speedrunning leaderboard";. ^
    ui.py
    ::--key KEY
    ::--version-file FILE

pyinstaller ^
    --distpath ..\ ^
    --noconfirm ^
    --clean ^
    --onefile ^
    "Global speedrunning leaderboard.spec"
    ::--key KEY
    ::--version-file FILE

pyi-makespec ^
    --onefile ^
    --name "Global speedrunning leaderboard [noconsole]" ^
    --icon favicon.ico ^
    --add-binary favicon.ico;. ^
    --add-binary LICENSE.txt;. ^
    --add-binary README.md;. ^
    --add-binary "C:\ProgramData\Global speedrunning leaderboard";. ^
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
    --name "Global speedrunning leaderboard [noconsole]" ^
    "Global speedrunning leaderboard [noconsole].spec"
    ::--key KEY
    ::--version-file FILE

PAUSE