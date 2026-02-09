@echo off
chcp 65001 > nul
pushd "%~dp0"

if not exist venv (
    python -m venv venv
)

call venv\Scripts\activate

python -m pip install -r requirements.txt

REM Запуск Python в отдельном процессе cmd
cmd /c python -m start.windows.start_windows

popd
