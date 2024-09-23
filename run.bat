@echo off
:: 设置颜色
set RED=0C
set GREEN=0A
set YELLOW=0E
set NC=0F

echo.
echo %GREEN%==== 项目启动脚本 ====%NC%

:: 获取 Python 解释器路径
for /f "delims=" %%i in ('where python') do set PYTHON=%%i
echo %PYTHON%

:: 检查是否安装了 Python
if "%PYTHON%"=="" (
    echo %RED%错误: 系统未检测到 Python。请先安装 Python 3.10 或更高版本。%NC%
    exit /b 1
)

:: 检查 Python 版本是否 >= 3.10
for /f "tokens=2 delims= " %%v in ('%PYTHON% --version') do set PYTHON_VERSION=%%v
echo Python版本: %PYTHON_VERSION%

:: 版本检查
echo %PYTHON_VERSION% | findstr /R "^3\.1[0-9]\|^3\.2[0-9]\|^3\.3[0-9]\|^3\.4[0-9]\|^3\.5[0-9]\|^3\.6[0-9]\|^3\.7[0-9]\|^3\.8[0-9]\|^3\.9[0-9]\|^3\.1[0-9][0-9]$" >nul
if errorlevel 1 (
    echo %RED%错误: Python 版本必须 >= 3.10，但当前版本是 %PYTHON_VERSION%。%NC%
    exit /b 1
)

:: 检查是否存在虚拟环境
if exist "venv" (
    echo %YELLOW%虚拟环境已存在，直接激活并启动...%NC%
    call venv\Scripts\activate
) else (
    echo %YELLOW%虚拟环境不存在，创建中...%NC%
    %PYTHON% -m venv venv
    if errorlevel 1 (
        echo %RED%虚拟环境创建失败。请检查 Python 安装是否正确。%NC%
        exit /b 1
    )
    call venv\Scripts\activate

    :: 检查并设置国内镜像源 (可选)
    set /p use_mirror="是否配置国内镜像源？[y/n] "
    if /i "%use_mirror%"=="y" (
        echo %YELLOW%正在配置国内镜像源...%NC%
        pip config set global.index-url https://mirror.nju.edu.cn/pypi/web/simple
    ) else (
        echo %YELLOW%跳过镜像源配置%NC%
    )

    :: 升级pip
    echo %YELLOW%升级pip...%NC%
    pip install --upgrade pip

    :: 安装项目依赖
    if exist "requirements.txt" (
        echo %YELLOW%安装依赖...%NC%
        pip install -r requirements.txt
    ) else (
        echo %RED%未找到 requirements.txt 文件，跳过依赖安装。%NC%
    )

    :: 安装 Playwright 浏览器（如果需要）
    echo %YELLOW%安装 Playwright 浏览器...%NC%
    playwright install chromium
)

:: 启动项目
echo %YELLOW%启动项目...%NC%
call venv\Scripts\python main.py

:: 退出虚拟环境
echo %YELLOW%退出虚拟环境...%NC%
call venv\Scripts\deactivate

echo %GREEN%==== 项目运行完毕 ====%NC%
