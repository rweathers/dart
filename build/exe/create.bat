pyinstaller --onefile --icon=../resources/dart.ico --noconsole ../../source/dart.py
copy dist\dart.exe dart-gui.exe
pyinstaller --onefile --icon=../resources/dart.ico ../../source/dart.py
copy dist\dart.exe dart.exe
rmdir /Q /S dist
rmdir /Q /S build
rmdir /Q /S __pycache__
del dart.spec
