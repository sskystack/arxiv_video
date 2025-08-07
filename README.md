# ArXiv Video Downloader

一个用于自动下载 ArXiv 论文项目页面视频的多线程工具。支持 YouTube、Bilibili 等外部视频平台，以及直接链接的视频文件。

## 特性

- 🚀 多线程并发下载，速度快
- 📺 支持 YouTube、Bilibili 等视频平台
- 🎯 自动提取项目页面视频链接
- 📱 支持高分辨率视频下载（1080p+）
- 📊 实时下载进度条显示
- 📝 详细的下载日志记录
- 🔄 自动重试机制

## 系统要求

- Python 3.7+
- ffmpeg（用于视频处理）

## 安装部署

### Linux 系统部署

1. **更新系统包管理器**

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

2. **安装 Python 和 pip**

```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv -y

# CentOS/RHEL
sudo yum install python3 python3-pip python3-venv -y
```

3. **安装 ffmpeg**

```bash
# Ubuntu/Debian
sudo apt install ffmpeg -y

# CentOS/RHEL
sudo yum install epel-release -y
sudo yum install ffmpeg -y
```

4. **克隆项目并设置环境**

```bash
git clone https://github.com/your-repo/arxiv_video.git
cd arxiv_video
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### macOS 系统部署

1. **安装 Homebrew（如果未安装）**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. **安装 Python 和 ffmpeg**

```bash
brew install python ffmpeg
```

3. **克隆项目并设置环境**

```bash
git clone https://github.com/your-repo/arxiv_video.git
cd arxiv_video
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 快速使用

### 下载最新一天的视频

1. **启动下载程序**

```bash
# Linux/macOS
source venv/bin/activate && python multi_thread_downloader.py

# 或者分步执行
source venv/bin/activate
python multi_thread_downloader.py
```

或者使用提供的脚本：

```bash
chmod +x run_multi_thread.sh
./run_multi_thread.sh
```

### 命令行参数模式

程序还支持非交互式的命令行参数：

```bash
# 下载最新的5篇论文（默认25篇）
source venv/bin/activate && python multi_thread_downloader.py --mode latest --max-papers 5 --workers 4

# 下载最新发布日的所有论文（推荐）
source venv/bin/activate && python multi_thread_downloader.py --mode latest_day --workers 8

# 下载指定日期的论文
source venv/bin/activate && python multi_thread_downloader.py --mode date --date 2025-08-06 --max-papers 10

# 下载指定论文ID
source venv/bin/activate && python multi_thread_downloader.py --mode id --paper-id 2308.04152

# 自定义下载目录
source venv/bin/activate && python multi_thread_downloader.py --mode latest_day --download-dir /path/to/your/download/folder
```

**参数说明：**

- `--mode`: 运行模式
  - `latest`: 获取最新的N篇论文
  - `latest_day`: 获取最新发布日的所有论文
  - `date`: 获取指定日期的论文
  - `id`: 下载指定论文ID
- `--workers`: 线程数（1-16，默认4）
- `--max-papers`: 最大论文数（默认25）
- `--date`: 目标日期（YYYY-MM-DD格式）
- `--paper-id`: 论文ID（如：2308.04152）
- `--download-dir`: 自定义下载目录路径

**程序会自动执行以下步骤：**

- 获取最新一天的 ArXiv 论文
- 检查每篇论文是否有项目页面
- 自动提取视频链接
- 使用多线程下载视频
- 显示下载进度条

### 配置说明

程序会自动使用合理的默认配置：

- **线程数**：4个（可在命令行或交互模式中调整）
- **下载目录**：`~/Movies/arxiv_video`（可自定义）
- **日志文件**：`./logs/`
- **视频质量**：自动选择最高质量

### 自定义下载目录

有两种方式可以修改视频保存位置：

#### 方法1：使用命令行参数（推荐）

```bash
# 使用 --download-dir 参数指定下载目录
source venv/bin/activate && python multi_thread_downloader.py --mode latest_day --download-dir /path/to/your/videos

# 例如：下载到桌面的 arxiv_videos 文件夹
source venv/bin/activate && python multi_thread_downloader.py --mode latest_day --download-dir ~/Desktop/arxiv_videos
```

#### 方法2：交互模式设置

运行程序时，在交互界面中输入自定义路径：

```bash
source venv/bin/activate && python multi_thread_downloader.py

# 程序会提示：
# 📁 下载目录 (默认: /Users/zhouzhongtian/Movies/arxiv_video): 
# 在此处输入你想要的目录路径，或直接回车使用默认路径
```

#### 方法3：修改代码中的默认路径

编辑 `crawler/multi_thread_arxiv_crawler.py` 文件，找到第95行左右的 `__init__` 方法：

```python
def __init__(self, download_folder="/你的/自定义/路径", max_workers=4):
```

## 常见问题

### 下载失败

1. 检查网络连接
2. 确认 ffmpeg 已正确安装
3. 查看日志文件了解详细错误信息

### 视频无法播放

1. 确保下载完整（检查文件大小）
2. 使用支持的视频播放器（如 VLC）

### 权限问题

```bash
# Linux/macOS 给脚本执行权限
chmod +x run_multi_thread.sh
```

## 项目结构

```text
arxiv_video/
├── multi_thread_downloader.py    # 主下载程序
├── run_multi_thread.sh          # 启动脚本
├── requirements.txt             # 依赖列表
├── crawler/                     # 爬虫模块
├── generator/                   # 生成器模块
├── analyzer/                    # 分析器模块
└── logs/                       # 日志目录
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
