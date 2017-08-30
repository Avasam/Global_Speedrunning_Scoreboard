pyi-makespec ^
    --onefile ^
    --icon favicon.ico ^
    --add-binary favicon.ico;. ^
    --add-binary LICENSE.txt;. ^
    --add-binary README.md;. ^
    --add-binary "C:\ProgramData\Global speedrunning leaderboard";. ^
    --name "Global speedrunning leaderboard" ^
    ui.py
    ::--key KEY
    ::--version-file FILE

pyinstaller ^
    --distpath ..\ ^
    --noconfirm ^
    --clean ^
    "Global speedrunning leaderboard.spec"
    ::--key KEY
    ::--version-file FILE

pyi-makespec ^
    --onefile ^
    --icon favicon.ico ^
    --add-binary favicon.ico;. ^
    --add-binary LICENSE.txt;. ^
    --add-binary README.md;. ^
    --add-binary "C:\ProgramData\Global speedrunning leaderboard";. ^
    --name "Global speedrunning leaderboard [noconsole]" ^
    --noconsole ^
    ui.py
    ::--key KEY
    ::--version-file FILE

pyinstaller ^
    --distpath ..\ ^
    --noconfirm ^
    --clean ^
    "Global speedrunning leaderboard [noconsole].spec"
    ::--key KEY
    ::--version-file FILE

PAUSE
