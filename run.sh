#!/bin/bash

# ArXiv Video Downloader 快速启动脚本
# 自动激活虚拟环境并使用推荐配置启动

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行安装脚本："
    echo "   bash install.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 清屏并显示欢迎信息
clear
echo "🚀 ArXiv Video Downloader"
echo "========================="
echo "📅 今日日期: $(date '+%Y年%m月%d日')"
echo "🎯 领域: 计算机视觉 (cs.CV)"
echo "🧵 线程数: 8"
echo "📁 下载目录: ~/Movies/arxiv_video"
echo ""
echo "⚡ 正在启动高速下载..."
echo "========================="
echo ""

# 运行主程序，使用推荐配置
python main.py --workers 8 --verbose

echo ""
echo "🎉 下载完成！感谢使用 ArXiv Video Downloader"
