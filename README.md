# 🎬 ArXiv Video Downloader

一个用于自动从 ArXiv 论文页面抓取演示视频并生成带中文解说与字幕的短视频工具。

本 README 包含：快速上手、按平台的环境安装与激活步骤（macOS / Linux / Windows / WSL）、以及完整的命令行参数使用教程和常见故障排查。

## 目录

- 项目简介
- 快速上手（推荐）
- 平台安装与环境配置（macOS / Linux / Windows / WSL）
- 虚拟环境：创建与激活（cross-platform）
- 安装 Python 依赖
- 命令行参数与使用示例
- 输出目录结构
- 故障排查（ImageMagick / 字体 / 日志）

---

## 项目简介

该项目会：
- 抓取论文页面中的视频资源（支持多来源）
- 下载并合并演示视频
- 通过 TTS 生成中文解说（分句生成音频）
- 生成与音频同步的字幕并合成到最终视频

依赖要点：Python 3.7+、FFmpeg、ImageMagick（字幕渲染需要）、以及系统字体（中英混排）。

---

## 快速上手（推荐）

1. 克隆仓库：

```bash
git clone https://github.com/sskystack/arxiv_video.git
cd arxiv_video
```

2. 参照下方“平台安装”为你的系统安装系统依赖（尤其是 ImageMagick 和 FFmpeg）。

3. 创建并激活 Python 虚拟环境（见下文详细方法）。

4. 安装 Python 依赖：

```bash
pip install -r requirements.txt
```

5. 运行（示例）：

```bash
python main.py --workers 8 --download-dir /path/to/downloads --max-papers 100
```

---

## 平台安装与环境配置（逐步）

下面分别给出 macOS、Linux、Windows 和 Windows+WSL 的详细步骤与常用命令（包括虚拟环境创建与激活）。

注意：所有命令假设你在仓库根路径 `arxiv_video/` 下执行，或自行 cd 到该目录。


### macOS — 从虚拟环境开始（清晰步骤）

步骤 1 — 在仓库目录创建并激活虚拟环境：

```bash
# 在仓库根目录执行
python3 -m venv .venv
source .venv/bin/activate
```

步骤 2 — 安装系统依赖（使用 Homebrew）：

```bash
brew update
brew install imagemagick ffmpeg git
```

步骤 3 — 在虚拟环境中安装 Python 依赖：

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

步骤 4 — 运行示例（在虚拟环境仍激活时）：

```bash
python main.py --workers 4 --download-dir ~/Movies/arxiv_video --max-papers 50
```

---

### Linux（Ubuntu / Debian）— 从虚拟环境开始（清晰步骤）

步骤 1 — 在仓库目录创建并激活虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

步骤 2 — 安装系统依赖：

```bash
sudo apt update
sudo apt install -y ffmpeg imagemagick git build-essential
```

说明：`build-essential` 常用于编译一些需要本地构建的 Python 扩展。

步骤 3 — 在虚拟环境中安装 Python 依赖：

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

步骤 4 — 运行示例：

```bash
python main.py --workers 4 --download-dir ~/Movies/arxiv_video --max-papers 50
```

---

### Windows（PowerShell，原生）— 从虚拟环境开始（清晰步骤）

步骤 1 — 在仓库目录创建并激活虚拟环境（PowerShell）：

```powershell
python -m venv .venv
# 激活（PowerShell）
.\.venv\Scripts\Activate.ps1
```

步骤 2 — 安装系统依赖（可选：使用 Chocolatey）：

```powershell
# 如果已安装 Chocolatey：
choco install -y git ffmpeg imagemagick

# 若未安装 Chocolatey，请先手动安装 ImageMagick/FFmpeg 或通过官网下载安装包。
```

注意：Windows 下安装 ImageMagick 时请确保将可执行程序路径加入 PATH。

步骤 3 — 在虚拟环境中安装 Python 依赖：

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

步骤 4 — 运行示例（PowerShell）：

```powershell
python main.py --workers 4 --download-dir C:\Users\<you>\Movies\arxiv_video --max-papers 50
```

---

### Windows + WSL（Ubuntu）— 从虚拟环境开始（清晰步骤，推荐）

步骤 1 — 在 WSL 的仓库目录创建并激活虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

步骤 2 — 在 WSL 中安装系统依赖：

```bash
sudo apt update
sudo apt install -y ffmpeg imagemagick git build-essential
```

步骤 3 — 在虚拟环境中安装 Python 依赖：

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

步骤 4 — 运行示例：

```bash
python main.py --workers 4 --download-dir ~/Movies/arxiv_video --max-papers 50
```

说明：WSL 环境的 FFmpeg / ImageMagick 更接近 Linux，适合批量处理与脚本化运行。

---

## 安装 Python 依赖

在激活虚拟环境后执行：

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

如果你遇到某些包安装失败（例如需要编译的扩展），请先安装对应系统的构建工具（macOS 的 Xcode command line tools，Ubuntu 的 build-essential 等）。

---

## 命令行参数与使用示例

运行入口：`python main.py`

常用参数说明：

| 参数 | 简写 | 类型 | 默认 | 说明 |
|------|------|------|------|------|
| `--publication-date` | `-p` | str | (自动) | 指定要下载的论文发布日期（YYYYMMDD） |
| `--workers` | `-w` | int | 4 | 下载线程数（1-16） |
| `--download-dir` | `-d` | str | ~/Movies/arxiv_video | 下载并保存视频的目录 |
| `--max-papers` | `-m` | int | 1000 | 最大处理论文数 |
| `--field` | `-f` | str | cs.CV | ArXiv 领域，例如 cs.CV / cs.AI / cs.LG |
| `--verbose` | `-v` | flag | False | 打印详细日志（DEBUG） |

示例：

- 使用 8 个线程，最多下载 100 篇 CS.CV 视频：

```bash
python main.py --workers 8 --max-papers 100 --field cs.CV
```

- 下载指定发布日期的论文（2025-08-20）：

```bash
python main.py --publication-date 20250820 --workers 6 --max-papers 200
```

- 将结果保存到自定义目录并打开详细日志：

```bash
python main.py -d ~/AI_Videos -w 8 -m 50 -v
```

如果你仍然需要使用仓库中的 `multi_thread_downloader.py`（它是一个单文件的多线程交互/非交互脚本），在删除或合并前可以直接运行：

```bash
python multi_thread_downloader.py
# 或 非交互（如果支持参数）
python multi_thread_downloader.py --workers 4 --mode latest --max-papers 50
```

---

## 输出目录结构（示例）

```
{download-dir}/
└── YYYYMMDD/
      ├── <paper_id>/
      │   ├── video_0.mp4          # 原始演示视频
      │   ├── video_1.mp4
      │   ├── <paper_id>_demo.mp4  # 合并演示（可选）
      │   ├── <paper_id>_res.mp4   # 最终合成视频（演示+解说+字幕）
      │   ├── <paper_id>.json      # 解说卡片/元数据
      │   └── audio/               # 分句语音文件
      └── ...
```

---

## 故障排查（常见问题）

1) 字幕/中文不显示

- 确保 ImageMagick 已安装并在 PATH 中：

```bash
magick -version
```

- 测试字体可用性（仓库含 `test_fonts.py`）：

```bash
python test_fonts.py
```

2) FFmpeg 问题（合成/转码失败）

- 确保 ffmpeg 可用并版本为较新版本：

```bash
ffmpeg -version
```

3) 依赖安装错误

- 在安装 Python 依赖失败时，查看错误信息并安装系统构建工具：

   - macOS: `xcode-select --install`
   - Ubuntu: `sudo apt install build-essential libffi-dev python3-dev`

4) 日志与调试

- 使用 `--verbose` 打印详细日志：

```bash
python main.py --verbose
```

日志文件位于 `logs/`（按运行日期创建），可以打开查看详细执行信息。

---

## 额外说明

- 本项目支持数据库集成（见 `reduct_db/` 子模块），若启用数据库，程序会优先使用数据库内的 `publication_date` 来组织输出目录。
- 如果你需要我把仓库中旧的 `crawler/` 脚本合并到 `core/` 或删除 `multi_thread_downloader.py`，请明确回复，我会执行合并/删除并运行基础 smoke-test。

---

如果需要，我可以再生成一个简短的一键安装脚本或为 Windows 用户生成 PowerShell 自动化步骤。欢迎告诉我更具体的需求。
# 🎬 ArXiv Video Downloader

自动从 ArXiv 获取论文页面中展示的视频并生成带解说与字幕的短视频工具。

[![Python](https://img.shields.io/badge/Python-3.7+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![ImageMagick](https://img.shields.io/badge/ImageMagick-Required-red?style=for-the-badge)](https://imagemagick.org/)

本仓库将爬取论文页面中的视频资源，下载并合成：原始演示视频 + 自动生成的中文解说音频 + 同步字幕（支持中英混排，依赖系统字体与 ImageMagick）。

## 主要特性

- 支持多平台（Linux / macOS / Windows）的视频下载与合成
- 多线程下载（可配置线程数量）
- 自动生成中文解说（通过 TTS 服务）并为每句生成同步字幕
- 可将结果保存为结构化目录（按 publication_date / paper_id 分组）

## 快速开始

1. 安装依赖（建议在虚拟环境中）

```bash
pip install -r requirements.txt
```

2. 安装系统依赖（必须）

macOS:

```bash
brew install imagemagick ffmpeg
```

Ubuntu/Debian:

```bash
sudo apt install imagemagick ffmpeg
```

Windows（建议使用 Chocolatey）:

```powershell
choco install imagemagick ffmpeg
```

3. 运行项目（示例）

```bash
python main.py --workers 8 --download-dir /path/to/downloads --max-papers 100
```

## 项目结构（简洁）

```
arxiv_video/
├─ core/                    # 项目核心模块（抓取、合成、TTS 等）
├─ crawler/                 # 较早期/独立的多线程爬虫脚本（被 multi_thread_downloader.py 引用）
├─ logs/                    # 日志文件
├─ reduct_db/               # 数据库集成模块
├─ main.py                  # 主入口（使用 core.crawler）
├─ multi_thread_downloader.py# 可选的多线程下载器（引用 crawler/ 目录）
└─ README.md
```

## 下一步建议

1. 如果你想清理并移除 `crawler/`，我可以：
    - 将 `crawler/multi_thread_arxiv_crawler.py` 的核心实现合并到 `core/`，并更新 `multi_thread_downloader.py` 与 `README`；或
    - 直接删除 `crawler/` 并在 `multi_thread_downloader.py` 中移除对它的引用（风险：会丢失脚本功能）。

2. 我已修复 README 的格式。如果你希望我同时移除 README 中对 `crawler` 的提及（例如确认代码合并完成后），我会在合并/删除 `crawler/` 时一起更新。

请告诉我接下来要执行的方案（合并 / 删除 / 保留），我会继续执行相关修改并跑一次基本测试。


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
