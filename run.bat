@echo off
:: Set UTF-8
chcp 65001 > nul
setlocal EnableDelayedExpansion

:: Check if Windows Terminal is installed and restart script with it
where wt.exe >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    :: Check if not already running in Windows Terminal
    if not defined WT_SESSION (
        wt -p "Command Prompt" "%~f0"
        exit /b
    )
)

:: Get system language
for /f "tokens=2 delims==" %%a in ('wmic os get oslanguage /value') do set "LANG=%%a"

:: Color definitions
if defined WT_SESSION (
    :: Use PowerShell for colored output in Windows Terminal
    set "PRINT_GREEN=powershell Write-Host -NoNewline -ForegroundColor Green"
    set "PRINT_RED=powershell Write-Host -NoNewline -ForegroundColor Red"
    set "PRINT_YELLOW=powershell Write-Host -NoNewline -ForegroundColor Yellow"
    set "PRINTLN=echo."
) else (
    :: Use traditional colors in CMD
    set "GREEN=color 0a"
    set "RED=color 0c"
    set "YELLOW=color 0e"
    set "WHITE=color 07"
)

echo.
if defined WT_SESSION (
    if "%LANG%"=="2052" (
        %PRINT_GREEN% "==== 项目启动脚本 ===="
    ) else (
        %PRINT_GREEN% "==== Project Startup Script ===="
    )
    %PRINTLN%
) else (
    %GREEN%
    if "%LANG%"=="2052" (
        echo ==== 项目启动脚本 ====
    ) else (
        echo ==== Project Startup Script ====
    )
    %WHITE%
)

:: Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if defined WT_SESSION (
        if "%LANG%"=="2052" (
            %PRINT_RED% "错误: 系统未检测到 Python。请先安装 Python 3.10。"
        ) else (
            %PRINT_RED% "Error: Python not found. Please install Python 3.10 first."
        )
        %PRINTLN%
    ) else (
        %RED%
        if "%LANG%"=="2052" (
            echo 错误: 系统未检测到 Python。请先安装 Python 3.10。
        ) else (
            echo Error: Python not found. Please install Python 3.10 first.
        )
        %WHITE%
    )
    exit /b 1
)

:: Get Python version
for /f "tokens=1,2,3,4 delims=. " %%a in ('python -V 2^>^&1') do (
    set "PYTHON_MAJOR=%%b"
    set "PYTHON_MINOR=%%c"
    set "PYTHON_MICRO=%%d"
)

if "%LANG%"=="2052" (
    echo Python版本: !PYTHON_MAJOR!.!PYTHON_MINOR!.!PYTHON_MICRO!
) else (
    echo Python version: !PYTHON_MAJOR!.!PYTHON_MINOR!.!PYTHON_MICRO!
)

:: Version check
if !PYTHON_MAJOR! NEQ 3 (
    if defined WT_SESSION (
        if "%LANG%"=="2052" (
            %PRINT_RED% "错误: Python 版本必须为 3.10，但当前版本是 !PYTHON_MAJOR!.!PYTHON_MINOR!.!PYTHON_MICRO!"
        ) else (
            %PRINT_RED% "Error: Python version must be 3.10, but got !PYTHON_MAJOR!.!PYTHON_MINOR!.!PYTHON_MICRO!"
        )
        %PRINTLN%
    ) else (
        %RED%
        if "%LANG%"=="2052" (
            echo 错误: Python 版本必须为 3.10，但当前版本是 !PYTHON_MAJOR!.!PYTHON_MINOR!.!PYTHON_MICRO!
        ) else (
            echo Error: Python version must be 3.10, but got !PYTHON_MAJOR!.!PYTHON_MINOR!.!PYTHON_MICRO!
        )
        %WHITE%
    )
    exit /b 1
)
if !PYTHON_MINOR! NEQ 10 (
    if defined WT_SESSION (
        if "%LANG%"=="2052" (
            %PRINT_RED% "错误: Python 版本必须为 3.10，但当前版本是 !PYTHON_MAJOR!.!PYTHON_MINOR!"
        ) else (
            %PRINT_RED% "Error: Python version must be 3.10, but got !PYTHON_MAJOR!.!PYTHON_MINOR!"
        )
        %PRINTLN%
    ) else (
        %RED%
        if "%LANG%"=="2052" (
            echo 错误: Python 版本必须为 3.10，但当前版本是 !PYTHON_MAJOR!.!PYTHON_MINOR!
        ) else (
            echo Error: Python version must be 3.10, but got !PYTHON_MAJOR!.!PYTHON_MINOR!
        )
        %WHITE%
    )
    exit /b 1
)

:: Check virtual environment
if exist "venv" (
    if defined WT_SESSION (
        %PRINT_YELLOW% "虚拟环境已存在，直接激活并启动..."
        %PRINTLN%
    ) else (
        %YELLOW%
        echo 虚拟环境已存在，直接激活并启动...
        %WHITE%
    )
    call venv\Scripts\activate
) else (
    if defined WT_SESSION (
        %PRINT_YELLOW% "虚拟环境不存在，创建中..."
        %PRINTLN%
    ) else (
        %YELLOW%
        echo 虚拟环境不存在，创建中...
        %WHITE%
    )
    python -m venv venv
    if errorlevel 1 (
        if defined WT_SESSION (
            %PRINT_RED% "虚拟环境创建失败。请检查 Python 安装是否正确。"
            %PRINTLN%
        ) else (
            %RED%
            echo 虚拟环境创建失败。请检查 Python 安装是否正确。
            %WHITE%
        )
        exit /b 1
    )
    call venv\Scripts\activate

    :: Mirror configuration
    choice /c yn /m "是否配置国内镜像源？"
    if !ERRORLEVEL! EQU 1 (
        if defined WT_SESSION (
            %PRINT_YELLOW% "正在配置国内镜像源..."
            %PRINTLN%
        ) else (
            %YELLOW%
            echo 正在配置国内镜像源...
            %WHITE%
        )
        pip config set global.index-url https://mirror.nju.edu.cn/pypi/web/simple
    ) else (
        if defined WT_SESSION (
            %PRINT_YELLOW% "跳过镜像源配置"
            %PRINTLN%
        ) else (
            %YELLOW%
            echo 跳过镜像源配置
            %WHITE%
        )
    )

    :: Upgrade pip
    if defined WT_SESSION (
        %PRINT_YELLOW% "升级pip..."
        %PRINTLN%
    ) else (
        %YELLOW%
        echo 升级pip...
        %WHITE%
    )
    python -m pip install --upgrade pip

    :: Install dependencies
    if exist "requirements.txt" (
        if defined WT_SESSION (
            %PRINT_YELLOW% "安装依赖..."
            %PRINTLN%
        ) else (
            %YELLOW%
            echo 安装依赖...
            %WHITE%
        )
        pip install -r requirements.txt
    ) else (
        if defined WT_SESSION (
            %PRINT_RED% "未找到 requirements.txt 文件，跳过依赖安装。"
            %PRINTLN%
        ) else (
            %RED%
            echo 未找到 requirements.txt 文件，跳过依赖安装。
            %WHITE%
        )
    )

    :: Install Playwright
    if defined WT_SESSION (
        %PRINT_YELLOW% "安装 Playwright 浏览器..."
        %PRINTLN%
    ) else (
        %YELLOW%
        echo 安装 Playwright 浏览器...
        %WHITE%
    )
    playwright install chromium
)

:: Start project
if defined WT_SESSION (
    %PRINT_YELLOW% "启动项目..."
    %PRINTLN%
) else (
    %YELLOW%
    echo 启动项目...
    %WHITE%
)
python main.py

:: Exit virtual environment
if defined WT_SESSION (
    %PRINT_YELLOW% "退出虚拟环境..."
    %PRINTLN%
) else (
    %YELLOW%
    echo 退出虚拟环境...
    %WHITE%
)
deactivate

if defined WT_SESSION (
    %PRINT_GREEN% "==== 项目运行完毕 ===="
    %PRINTLN%
) else (
    %GREEN%
    echo ==== 项目运行完毕 ====
    %WHITE%
)

if not defined WT_SESSION (
    echo.
    echo 提示：安装 Windows Terminal 可获得更好的显示效果
    echo 可以从 Microsoft Store 安装 Windows Terminal
)
pause
endlocal
