#!/bin/bash

# Set colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get system language
LANG=$(locale | grep LANG= | cut -d= -f2)

# Messages in both languages
if [[ $LANG == *"zh"* ]]; then
    MSG_START="${GREEN}==== 项目启动脚本 ====${NC}"
    MSG_PYTHON_NOT_FOUND="${RED}错误: 系统未检测到 Python3.10。${NC}"
    MSG_PYTHON_VERSION="${YELLOW}Python版本: %s${NC}"
    MSG_PYTHON_VERSION_ERROR="${RED}错误: Python 版本必须为 3.10，但当前版本是 %s${NC}"
    MSG_VENV_EXISTS="${YELLOW}虚拟环境已存在，直接激活并启动...${NC}"
    MSG_VENV_CREATING="${YELLOW}虚拟环境不存在，创建中...${NC}"
    MSG_VENV_FAILED="${RED}虚拟环境创建失败。请检查 Python 安装是否正确。${NC}"
    MSG_MIRROR_PROMPT="是否配置国内镜像源？[y/n] "
    MSG_MIRROR_CONFIG="${YELLOW}正在配置国内镜像源...${NC}"
    MSG_MIRROR_SKIP="${YELLOW}跳过镜像源配置${NC}"
    MSG_UPGRADING_PIP="${YELLOW}升级pip...${NC}"
    MSG_INSTALLING_DEPS="${YELLOW}安装依赖...${NC}"
    MSG_NO_REQUIREMENTS="${RED}未找到 requirements.txt 文件，跳过依赖安装。${NC}"
    MSG_INSTALLING_PLAYWRIGHT="${YELLOW}安装 Playwright 浏览器...${NC}"
    MSG_STARTING="${YELLOW}启动项目...${NC}"
    MSG_EXITING="${YELLOW}退出虚拟环境...${NC}"
    MSG_COMPLETE="${GREEN}==== 项目运行完毕 ====${NC}"
else
    MSG_START="${GREEN}==== Project Startup Script ====${NC}"
    MSG_PYTHON_NOT_FOUND="${RED}Error: Python 3.10 not found.${NC}"
    MSG_PYTHON_VERSION="${YELLOW}Python version: %s${NC}"
    MSG_PYTHON_VERSION_ERROR="${RED}Error: Python version must be 3.10, but got %s${NC}"
    MSG_VENV_EXISTS="${YELLOW}Virtual environment exists, activating...${NC}"
    MSG_VENV_CREATING="${YELLOW}Creating virtual environment...${NC}"
    MSG_VENV_FAILED="${RED}Failed to create virtual environment. Please check Python installation.${NC}"
    MSG_MIRROR_PROMPT="Configure mirror source? [y/n] "
    MSG_MIRROR_CONFIG="${YELLOW}Configuring mirror source...${NC}"
    MSG_MIRROR_SKIP="${YELLOW}Skipping mirror configuration${NC}"
    MSG_UPGRADING_PIP="${YELLOW}Upgrading pip...${NC}"
    MSG_INSTALLING_DEPS="${YELLOW}Installing dependencies...${NC}"
    MSG_NO_REQUIREMENTS="${RED}requirements.txt not found, skipping dependency installation.${NC}"
    MSG_INSTALLING_PLAYWRIGHT="${YELLOW}Installing Playwright browser...${NC}"
    MSG_STARTING="${YELLOW}Starting project...${NC}"
    MSG_EXITING="${YELLOW}Exiting virtual environment...${NC}"
    MSG_COMPLETE="${GREEN}==== Project Complete ====${NC}"
fi

echo -e "$MSG_START"

# 获取 Python 解释器路径
PYTHON=$(command -v python3.10)
echo -e "$PYTHON"

# 检查是否安装了 Python
if [ -z "$PYTHON" ]; then
    echo -e "$MSG_PYTHON_NOT_FOUND"
    exit 1
fi

# 检查 Python 版本
VERSION=$($PYTHON -V 2>&1 | cut -d' ' -f2)
printf -v MSG "$MSG_PYTHON_VERSION" "$VERSION"
echo -e "$MSG"

if [[ ! "$VERSION" =~ ^3\.10\. ]]; then
    printf -v MSG "$MSG_PYTHON_VERSION_ERROR" "$VERSION"
    echo -e "$MSG"
    exit 1
fi

# 检查是否存在虚拟环境
if [ -d "venv" ]; then
    echo -e "$MSG_VENV_EXISTS"
    # 激活虚拟环境
    source venv/bin/activate
else
    echo -e "$MSG_VENV_CREATING"
    # 使用获取到的 Python 解释器创建虚拟环境
    $PYTHON -m venv venv

    if [ $? -ne 0 ]; then
        echo -e "$MSG_VENV_FAILED"
        exit 1
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 检查并设置国内镜像源 (可选)
    read -p "$MSG_MIRROR_PROMPT" use_mirror
    if [[ "$use_mirror" == "y" ]]; then
        echo -e "$MSG_MIRROR_CONFIG"
        pip config set global.index-url https://mirror.nju.edu.cn/pypi/web/simple
    else
        echo -e "$MSG_MIRROR_SKIP"
    fi

    # 升级pip
    echo -e "$MSG_UPGRADING_PIP"
    pip install --upgrade pip

    # 安装项目依赖
    if [ -f "requirements.txt" ]; then
        echo -e "$MSG_INSTALLING_DEPS"
        pip install -r requirements.txt
    else
        echo -e "$MSG_NO_REQUIREMENTS"
    fi

    # 安装 Playwright 浏览器（如果需要）
    echo -e "$MSG_INSTALLING_PLAYWRIGHT"
    playwright install chromium
fi

# 启动项目
echo -e "$MSG_STARTING"
./venv/bin/python main.py

# 退出虚拟环境
echo -e "$MSG_EXITING"
deactivate

echo -e "$MSG_COMPLETE"