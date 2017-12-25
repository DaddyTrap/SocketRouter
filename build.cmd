pyinstaller.exe -F .\tests\five_node_test.py
pyinstaller.exe -F .\routerUI\SetUI.py
mkdir dist\tests
xcopy /Y /S tests dist\tests\