pyi-makespec ^
    --onefile ^
    --name "Red Wolves WCL report Analyser" ^
    --icon icon.ico ^
    ui.py
    ::--key KEY
    ::--noconsole
    ::--version-file FILE

pyinstaller ^
    --distpath ..\ ^
    --noconfirm ^
    --clean ^
    --onefile ^
    compile.spec
    ::--key KEY
    ::--noconsole
    ::--version-file FILE

PAUSE