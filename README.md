<div align="center"ArXiv Video Downloader 是一个专为研究人员和学术爱好者设计的工具，能够自动下载ArXiv论文项目页面中的演示视频。支持多线程并发下载，兼容YouTube、Bilibili等主流视频平台。

## ✨ 功能特性iv Video Downloader

**自动下载ArXiv论文项目页面视频的智能工具**

[![Python](https://img.shields.io/badge/Python-3.7+-blue?style=for-the-badge&logo=python)](https://www.python.org/)

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [安装指南](#-安装指南) • [使用教程](#-使用教程) • [项目架构](#-项目架构)

</div>

---

## 📖 项目简介

ArXiv Video Downloader 是一个专为研究人员和学术爱好者设计的工具，能够自动下载ArXiv论文项目页面中的演示视频。支持多线程并发下载，兼容YouTube、Bilibili等主流视频平台。


## ✨ 功能特性

### 核心功能
- 🎬 **多平台支持** - YouTube、Bilibili、直链视频
- 🚀 **多线程下载** - 1-16个线程并发，速度可控
- 📱 **高清视频** - 优先下载1080p+高分辨率视频
- 🎯 **智能筛选** - 自动获取最新发布论文
- 📂 **有序管理** - 按日期和论文ID分类存储

### 用户体验
- 📊 **实时进度** - tqdm进度条显示下载状态
- 📝 **详细日志** - 按日期记录所有操作日志
- 🔄 **断点续传** - 支持下载中断后继续
- ⚡ **一键运行** - 简单命令即可开始下载

## 🚀 快速开始

### 环境要求

| 项目 | 要求 |
|------|------|
| Python | 3.7+ |
| 操作系统 | Windows / macOS / Linux |
| 网络 | 能访问ArXiv和视频平台 |
| 存储 | 建议10GB+空间 |

### 一分钟体验

```bash
# 1. 克隆项目
git clone https://github.com/sskystack/arxiv_video.git
cd arxiv_video

# 2. 安装依赖
pip install -r requirements.txt

# 3. 开始下载（推荐命令）
python main.py --workers 8 --download-dir {your_target_dir} --max-papers 1000
```

> 💡 **推荐使用命令**：将 `{your_target_dir}` 替换为您的目标目录，例如：`/Users/username/Movies/arxiv_video`

就这么简单！程序会自动下载今天发布的CS.CV领域论文视频。

## 📦 安装指南

### 方法一：自动安装脚本（推荐）

**Linux/macOS:**
```bash
```

**Windows:**
```powershell
# 下载并运行安装脚本
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/sskystack/arxiv_video/main/install.ps1" -OutFile "install.ps1"
.\install.ps1
```

### 方法二：手动安装

#### Step 1: 安装依赖软件

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv ffmpeg git
```

**CentOS/RHEL:**
```bash
sudo yum update -y && sudo yum install -y python3 python3-pip python3-venv epel-release
sudo yum install -y ffmpeg git
```

**macOS:**
```bash
# 安装 Homebrew（如未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# 安装依赖
brew install python ffmpeg git
```

**Windows:**
```powershell
# 安装 Chocolatey（如未安装）
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
# 安装依赖
choco install python git ffmpeg -y
```

#### Step 2: 克隆和配置项目

```bash
# 克隆项目
git clone https://github.com/sskystack/arxiv_video.git
cd arxiv_video

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安装Python依赖
pip install -r requirements.txt
```

## 📖 使用教程

### 基础用法

**🚀 推荐使用命令（完整配置）：**
```bash
python main.py --workers 8 --download-dir {your_target_dir} --max-papers 1000
```

**最简单的使用方式：**
```bash
python main.py
```
这将使用默认配置下载今天的CS.CV论文视频。

### 高级用法

**指定论文领域：**
```bash
# 下载人工智能领域论文
python main.py --field cs.AI

# 下载机器学习领域论文  
python main.py --field cs.LG

# 下载计算机视觉领域论文
python main.py --field cs.CV
```

**控制下载数量：**
```bash
# 最多处理50篇论文
python main.py --max-papers 50

# 处理所有论文（不建议）
python main.py --max-papers 999999
```

**组合使用：**
```bash
# 高性能下载AI领域论文到指定目录
python main.py 
  --field cs.AI 
  --workers 8 
  --max-papers 100 
  --download-dir ~/AI_Videos 
  --verbose
```

### 命令行参数完整列表

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--workers` | `-w` | 4 | 下载线程数（1-16） |
| `--download-dir` | `-d` | `{your_target_dir}` | 视频保存目录 |
| `--max-papers` | `-m` | 1000 | 最大处理论文数 |
| `--field` | `-f` | `cs.CV` | ArXiv论文领域 |
| `--verbose` | `-v` | False | 显示详细日志 |
| `--help` | `-h` | - | 显示帮助信息 |

### 输出结构

下载的视频将按以下结构组织：
```
下载目录/
└── YYYYMMDD/              # 按日期分类
    ├── 论文ID1/           # 每篇论文一个文件夹
    │   ├── video_0.mp4    # 视频文件
    │   └── video_1.mp4
    └── 论文ID2/
        └── video_0.mp4
```

## 🔧 高级配置

### 环境变量配置

创建 `.env` 文件来配置高级选项：

```bash
# .env 文件
ARXIV_FIELD=cs.CV
MAX_WORKERS=8
DOWNLOAD_DIR=/path/to/videos
LOG_LEVEL=INFO
```

### 代理设置

如果需要使用代理：

```bash
# HTTP代理
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# SOCKS5代理
export HTTP_PROXY=socks5://proxy.example.com:1080
export HTTPS_PROXY=socks5://proxy.example.com:1080

# 然后运行程序
python main.py
```

## 🏗️ 项目架构

```
arxiv_video/
├── 📁 core/                    # 🧠 核心业务逻辑
│   ├── arxiv_fetcher.py       # 📚 ArXiv论文获取器
│   ├── link_extractor.py      # 🔗 项目链接提取器  
│   ├── video_extractor.py     # 🎬 视频链接解析器
│   ├── video_downloader.py    # ⬇️ 多线程下载器
│   └── crawler.py             # 🕷️ 主爬虫逻辑
├── 📁 utils/                   # 🛠️ 工具模块
│   └── logger.py              # 📝 日志管理器
├── 📁 logs/                    # 📊 日志文件夹
├── 📄 main.py                  # 🚀 程序入口
├── 📄 requirements.txt         # 📦 依赖列表
└── 📄 README.md               # 📖 项目文档
```

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个Star！ ⭐**

[⬆️ 回到顶部](#-arxiv-video-downloader)

</div>
