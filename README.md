<div align="center">

# 🎬 ArXiv Video Downloader

**自动下载ArXiv论文项目页面视频的智能工具**

[![Python](https://img.shields.io/badge/Python-3.7+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![ImageMagick](https://img.shields.io/badge/ImageMagick-Required-red?style=for-the-badge)](https://imagemagick.org/)

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [安装指南](#-安装指```
arxiv_video/
├── 📁 core/                       # 🧠 核心业务逻辑
│   ├── arxiv_fetcher.py          # 📚 ArXiv论文获取器（支持publication_date参数）
│   ├── link_extractor.py         # 🔗 项目链接提取器  
│   ├── video_extractor.py        # 🎬 视频链接解析器
│   ├── video_downloader.py       # ⬇️ 多线程下载器
│   ├── video_composer.py         # 🎥 **新增**：视频合成器（字幕+语音）
│   ├── card_generator.py         # 📝 **新增**：解说卡片生成器
│   ├── tts_service.py            # 🎤 **新增**：语音合成服务
│   ├── Card.py                   # 📊 **新增**：卡片数据结构
│   └── crawler.py                # 🕷️ 主爬虫逻辑（集成数据库支持）
├── 📁 utils/                      # 🛠️ 工具模块
│   └── logger.py                 # 📝 日志管理器
├── 📁 logs/                       # 📊 日志文件夹
├── 📁 cards/                      # 📄 **新增**：解说卡片存储
├── 📁 reduct_db/                  # 🗄️ 数据库模块
│   └── reduct_db/                # 📊 MySQL数据库集成
│       ├── db_dao/               # 🔍 数据访问对象
│       ├── db_entities/          # 📋 数据实体定义
│       └── db_config/            # ⚙️ 数据库配置
├── 📄 main.py                     # 🚀 程序入口（支持publication_date参数）
├── 📄 test_fonts.py               # 🔤 **新增**：字体测试工具
├── 📄 requirements.txt            # 📦 依赖列表
├── 📄 SUBTITLE_FIX_REPORT.md      # 📋 **新增**：字幕功能修复报告
└── 📄 README.md                   # 📖 项目文档
```• [项目架构](#-项目架构)

</div>

---

## 📖 项目简介

ArXiv Video Downloader 是一个专为研究人员和学术爱好者设计的工具，能够自动下载ArXiv论文项目页面中的演示视频，并生成带有智能解说字幕的完整视频内容。支持多线程并发下载，兼容YouTube、Bilibili等主流视频平台。

**🎯 核心特色**：
- 🗓️ **智能日期处理**：优先使用数据库中的publication_date，支持指定发布日期参数
- 🎥 **视频字幕合成**：自动生成语音解说和同步字幕，支持跨平台字体
- 📊 **数据库集成**：支持MySQL数据库，实现论文信息的持久化管理
- 🚀 **精准论文获取**：使用ArXiv API获取指定日期的最新发布论文


## ✨ 功能特性

### 核心功能

- 🎬 **多平台支持** - YouTube、Bilibili、直链视频
- 🚀 **多线程下载** - 1-16个线程并发，速度可控
- 📱 **高清视频** - 优先下载1080p+高分辨率视频
- 🎯 **智能筛选** - 基于论文发布日期自动获取最新论文
- 📂 **有序管理** - 按发布日期和论文ID分类存储
- 🗄️ **数据库集成** - 支持MySQL数据库存储，优先使用publication_date
- 🗓️ **日期参数** - 支持指定publication_date参数，精确获取特定日期论文

### 视频处理功能 🎥

- 🎤 **智能语音解说** - 自动生成中文语音解说
- 📝 **同步字幕** - 基于实际音频时长的精确字幕同步  
- 🔤 **跨平台字体** - 智能检测最佳中文字体（Arial Unicode MS优先）
- 🎬 **视频合成** - 演示视频 + 语音解说 + 字幕的完整合成
- 📊 **解说卡片** - 自动生成论文信息的结构化解说内容

### 用户体验

- 📊 **实时进度** - tqdm进度条显示下载状态
- 📝 **详细日志** - 按日期记录所有操作日志，显示日期来源
- 🔄 **断点续传** - 支持下载中断后继续
- ⚡ **一键运行** - 简单命令即可开始下载
- 🎯 **精准日期** - 优先使用数据库中的publication_date，提高准确性

## 🚀 快速开始

### 环境要求

| 项目 | 要求 | 说明 |
|------|------|------|
| Python | 3.7+ | 核心运行环境 |
| ImageMagick | 最新版 | **新增要求**：用于字幕渲染 |
| FFmpeg | 最新版 | 视频处理必需 |
| 操作系统 | Windows / macOS / Linux | 跨平台支持 |
| 网络 | 能访问ArXiv和视频平台 | 下载功能需要 |
| 存储 | 建议10GB+空间 | 视频文件较大 |

### 一分钟体验

```bash
# 1. 安装系统依赖（重要！）
# macOS:
brew install imagemagick ffmpeg

# Ubuntu/Debian:
sudo apt install imagemagick ffmpeg

# Windows:
choco install imagemagick ffmpeg

# 2. 克隆项目
git clone https://github.com/sskystack/arxiv_video.git
cd arxiv_video

# 3. 安装Python依赖
pip install -r requirements.txt

# 4. 开始下载（推荐命令）
python main.py --workers 8 --download-dir {your_target_dir} --max-papers 1000
```

> 💡 **重要提示**：ImageMagick是字幕功能的必需依赖，请务必先安装！

就这么简单！程序会自动下载今天发布的CS.CV领域论文视频。

## 📦 安装指南

### 方法一：一键安装（推荐）

**Linux/macOS:**
```bash
# 克隆项目并自动安装
git clone https://github.com/sskystack/arxiv_video.git
cd arxiv_video
pip install -r requirements.txt
```

**Windows:**
```powershell
# 克隆项目并自动安装
git clone https://github.com/sskystack/arxiv_video.git
cd arxiv_video
pip install -r requirements.txt
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

这将使用默认配置下载今天的CS.CV论文视频，并自动生成带字幕的合成视频。

### 高级用法

**指定发布日期（新功能）：**

```bash
# 下载2025年8月20日发布的论文
python main.py --publication-date 20250820

# 结合其他参数使用
python main.py --publication-date 20250820 --workers 8 --max-papers 50
```

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
# 高性能下载指定日期的AI领域论文到指定目录
python main.py \
  --publication-date 20250820 \
  --field cs.AI \
  --workers 8 \
  --max-papers 100 \
  --download-dir ~/AI_Videos \
  --verbose
```

### 命令行参数完整列表

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--publication-date` | `-p` | 今天 | **新增**：指定发布日期 (YYYYMMDD格式) |
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
└── YYYYMMDD/                    # 按论文发布日期分类
    ├── 论文ID1/                 # 每篇论文一个文件夹
    │   ├── video_0.mp4          # 原始演示视频
    │   ├── video_1.mp4          # 原始演示视频
    │   ├── 论文ID1_demo.mp4     # 合并的演示视频
    │   ├── 论文ID1_res.mp4      # 🆕 最终合成视频（演示+解说+字幕）
    │   ├── 论文ID1.json         # 🆕 解说卡片数据
    │   ├── video_list.txt       # 视频列表文件
    │   └── audio/               # 🆕 语音文件目录
    │       ├── sentence_0.mp3   # 分句语音文件
    │       ├── sentence_1.mp4   # 分句语音文件
    │       ├── narration.wav    # 完整解说语音
    │       └── audio_list.txt   # 音频列表文件
    └── 论文ID2/
        └── ...
```

> 📝 **日期说明**：系统优先使用数据库中的`publication_date`作为文件夹命名，如果数据库中没有该论文记录，则使用ArXiv API返回的发布日期。日志中会显示使用的日期来源。

> 🎥 **视频说明**：`_res.mp4` 是最终的完整视频，包含演示视频、中文语音解说和同步字幕，推荐观看此文件。

## 🔧 高级配置

### 字幕功能配置 🎬

本项目支持自动生成带字幕的视频合成功能：

#### 字幕特性
- ✅ **中文语音解说**：自动生成论文解说语音
- ✅ **精确同步**：字幕与音频时长完美同步
- ✅ **跨平台字体**：智能选择最佳字体
- ✅ **视觉效果**：白色文字 + 黑色描边 + 半透明背景

#### 字体支持策略
系统会自动检测并选择最佳字体：

| 平台 | 优先字体 | 备选字体 |
|------|----------|----------|
| **macOS** | Arial Unicode MS | PingFang SC, Heiti SC, Songti SC |
| **Windows** | Arial Unicode MS | Microsoft YaHei, SimSun, SimHei |
| **Linux** | Arial Unicode MS | Noto Sans CJK SC, WenQuanYi 系列 |

#### 故障排除
如果字幕无法显示，请检查：

```bash
# 1. 确认ImageMagick已安装
magick -version

# 2. 测试字体可用性
python test_fonts.py

# 3. 查看详细日志
python main.py --verbose
```

> 🔧 **技术细节**：字幕时间基于每个音频片段的实际时长计算，而非简单平均分配，确保字幕与语音完美同步。

### 环境变量配置

创建 `.env` 文件来配置高级选项：

```bash
# .env 文件
ARXIV_FIELD=cs.CV
MAX_WORKERS=8
DOWNLOAD_DIR=/path/to/videos
LOG_LEVEL=INFO
```

### 日期处理机制

本系统实现了智能的日期处理机制，确保使用最准确的论文发布日期：

1. **数据库优先策略**：
   - 首先查询数据库中的`publication_date`字段
   - 如果数据库中存在该论文记录，优先使用`publication_date`
   - 日志显示：`使用publication_date: YYYYMMDD`

2. **ArXiv API备用策略**：
   - 如果数据库中没有记录，使用ArXiv API的`LastUpdatedDate`
   - `LastUpdatedDate`代表论文的实际发布/更新日期
   - 日志显示：`使用ArXiv提交日期: YYYYMMDD`

3. **技术改进点**：
   - ✅ 从`SubmittedDate`改为`LastUpdatedDate`，更准确反映发布时间
   - ✅ 集成数据库支持，优先使用`publication_date`
   - ✅ 增强日志记录，明确显示日期来源

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
│   ├── arxiv_fetcher.py       # 📚 ArXiv论文获取器（使用LastUpdatedDate排序）
│   ├── link_extractor.py      # 🔗 项目链接提取器  
│   ├── video_extractor.py     # 🎬 视频链接解析器
│   ├── video_downloader.py    # ⬇️ 多线程下载器
│   └── crawler.py             # 🕷️ 主爬虫逻辑（集成数据库支持）
├── 📁 utils/                   # 🛠️ 工具模块
│   └── logger.py              # 📝 日志管理器
├── 📁 logs/                    # 📊 日志文件夹
├── 📁 reduct_db/              # 🗄️ 数据库模块
│   └── reduct_db/             # 📊 MySQL数据库集成
│       ├── db_dao/            # 🔍 数据访问对象
│       ├── db_entities/       # � 数据实体定义
│       └── db_config/         # ⚙️ 数据库配置
├── �📄 main.py                  # 🚀 程序入口
├── 📄 requirements.txt         # 📦 依赖列表
└── 📄 README.md               # 📖 项目文档
```

### 核心组件说明

- **arxiv_fetcher.py**: 支持publication_date参数，精确获取指定日期的论文
- **video_composer.py**: 新增的视频合成引擎，支持字幕渲染和跨平台字体
- **card_generator.py**: 智能生成论文解说内容，集成数据库信息
- **tts_service.py**: 文本转语音服务，生成高质量中文解说
- **crawler.py**: 集成数据库支持，优先使用数据库中的`publication_date`字段
- **test_fonts.py**: 字体兼容性测试工具，帮助诊断字幕问题
- **reduct_db**: 完整的数据库集成模块，支持论文信息的持久化存储

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个Star！ ⭐**

[⬆️ 回到顶部](#-arxiv-video-downloader)

</div>
