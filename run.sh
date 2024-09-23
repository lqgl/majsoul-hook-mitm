#!/bin/bash

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==== 项目启动脚本 ====${NC}"

# 获取 Python 解释器路径
PYTHON=$(command -v python3)
echo -e "$PYTHON"

# 检查是否安装了 Python
if [ -z "$PYTHON" ]; then
    echo -e "${RED}错误: 系统未检测到 Python。请先安装 Python 3.10 或更高版本。${NC}"
    exit 1
fi

# 检查是否存在虚拟环境
if [ -d "venv" ]; then
    echo -e "${YELLOW}虚拟环境已存在，直接激活并启动...${NC}"
    # 激活虚拟环境
    source venv/bin/activate
else
    echo -e "${YELLOW}虚拟环境不存在，创建中...${NC}"
    # 使用获取到的 Python 解释器创建虚拟环境
    $PYTHON -m venv venv

    if [ $? -ne 0 ]; then
        echo -e "${RED}虚拟环境创建失败。请检查 Python 安装是否正确。${NC}"
        exit 1
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 检查并设置国内镜像源 (可选)
    read -p "是否配置国内镜像源？[y/n] " use_mirror
    if [[ "$use_mirror" == "y" ]]; then
        echo -e "${YELLOW}正在配置国内镜像源...${NC}"
        pip config set global.index-url https://mirror.nju.edu.cn/pypi/web/simple
    else
        echo -e "${YELLOW}跳过镜像源配置${NC}"
    fi

    # 升级pip
    echo -e "${YELLOW}升级pip...${NC}"
    pip install --upgrade pip

    # 安装项目依赖
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}安装依赖...${NC}"
        pip install -r requirements.txt
    else
        echo -e "${RED}未找到 requirements.txt 文件，跳过依赖安装。${NC}"
    fi

    # 安装 Playwright 浏览器（如果需要）
    echo -e "${YELLOW}安装 Playwright 浏览器...${NC}"
    playwright install chromium
fi

# 启动项目
echo -e "${YELLOW}启动项目...${NC}"
./venv/bin/python main.py

# 退出虚拟环境
echo -e "${YELLOW}退出虚拟环境...${NC}"
deactivate

echo -e "${GREEN}==== 项目运行完毕 ====${NC}"