#!/bin/bash
# ArXiv Video Crawler - 多线程版本启动脚本

echo "🚀 启动 ArXiv Video Crawler - 多线程版本"
echo "========================================"

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "✅ 发现虚拟环境，正在激活..."
    source .venv/bin/activate
else
    echo "⚠️  未找到虚拟环境 (.venv)"
    echo "建议先创建虚拟环境: python -m venv .venv"
fi

# 检查依赖
echo "🔧 检查依赖包..."
python -c "import requests, selenium, beautifulsoup4, arxiv, tqdm" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 依赖包检查通过"
else
    echo "❌ 缺少必要依赖，正在安装..."
    pip install requests selenium beautifulsoup4 arxiv retry tqdm
fi

echo "🎬 启动多线程视频下载器..."
echo "========================================"

# 启动多线程下载器
python multi_thread_downloader.py
