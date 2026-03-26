@echo off
chcp 65001 >nul
title 小红书采集器 - 启动控制台

echo ==========================================
echo       正在初始化 小红书数据采集器...
echo ==========================================

:: 检查是否安装了 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先去官网下载安装 Python 3.10+ 并勾选 "Add to PATH"！
    pause
    exit
)

:: 检查并创建虚拟环境
if not exist "venv" (
    echo [信息] 首次运行，正在为您创建独立的运行环境，请稍候...
    python -m venv venv
    echo [信息] 正在安装核心依赖包 (可能需要几分钟)...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    call venv\Scripts\activate.bat
)

echo ==========================================
echo       环境就绪！正在为您拉起可视化界面...
echo ==========================================

:: 启动 Streamlit
streamlit run ui.py

pause