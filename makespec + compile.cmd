pyi-makespec ^
    --onefile ^
    --icon favicon.ico ^
    --add-binary favicon.ico;. ^
    --add-binary LICENSE.txt;. ^
    --add-binary README.md;. ^
    --add-binary "C:\ProgramData\Global Speedrunning Scoreboard";. ^
    --name "Global Speedrunning Scoreboard" ^
    ui.py
    ::--key KEY
    ::--version-file FILE

pyinstaller ^
    --distpath ..\ ^
    --noconfirm ^
    --clean ^
    "Global Speedrunning Scoreboard.spec"
    ::--key KEY
    ::--version-file FILE

pyi-makespec ^
    --onefile ^
    --icon favicon.ico ^
    --add-binary favicon.ico;. ^
    --add-binary LICENSE.txt;. ^
    --add-binary README.md;. ^
    --add-binary "C:\ProgramData\Global Speedrunning Scoreboard";. ^
    --name "Global Speedrunning Scoreboard [noconsole]" ^
    --noconsole ^
    ui.py
    ::--key KEY
    ::--version-file FILE

pyinstaller ^
    --distpath ..\ ^
    --noconfirm ^
    --clean ^
    "Global Speedrunning Scoreboard [noconsole].spec"
    ::--key KEY
    ::--version-file FILE

PAUSE
