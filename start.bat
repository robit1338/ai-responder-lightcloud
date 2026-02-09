@echo off
chcp 65001 > nul

REM Перейти в директорию файла (корень проекта)
pushd "%~dp0"

REM Создать venv только если его нет
if not exist venv (
    echo [INFO] Creating venv...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Make sure python is in PATH.
        popd
        exit /b 1
    )
)

REM Активировать venv
call venv\Scripts\activate

REM Установить только зависимости из requirements.txt (без лишних апгрейдов)
echo [INFO] Installing requirements...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Installing requirements failed.
    popd
    exit /b 2
)

REM Запуск бота
echo [INFO] Starting bot...
python -m start.windows.start_windows

REM Возврат в исходную папку
popd
exit /b 0
