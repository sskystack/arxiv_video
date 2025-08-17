#!/bin/bash

# ArXiv Video Downloader 自动安装脚本
# 支持 Linux 和 macOS

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        print_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    print_info "检测到操作系统: $OS"
}

# 检查是否已安装命令
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 安装系统依赖
install_system_deps() {
    print_info "安装系统依赖..."
    
    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv ffmpeg git curl
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y python3 python3-pip python3-venv epel-release git curl
            sudo yum install -y ffmpeg
            ;;
        "macos")
            if ! command_exists brew; then
                print_info "安装 Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python ffmpeg git
            ;;
    esac
    
    print_success "系统依赖安装完成"
}

# 克隆项目
clone_project() {
    print_info "克隆项目..."
    
    if [ -d "arxiv_video" ]; then
        print_warning "项目目录已存在，更新项目..."
        cd arxiv_video
        git pull origin main
    else
        git clone https://github.com/sskystack/arxiv_video.git
        cd arxiv_video
    fi
    
    print_success "项目代码准备完成"
}

# 设置Python环境
setup_python_env() {
    print_info "设置Python虚拟环境..."
    
    # 创建虚拟环境
    python3 -m venv venv
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    print_info "安装Python依赖包..."
    pip install -r requirements.txt
    
    print_success "Python环境设置完成"
}

# 验证安装
verify_installation() {
    print_info "验证安装..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 测试导入主要模块
    python3 -c "
import sys
sys.path.append('.')
try:
    from core.crawler import ArxivVideoCrawler
    from utils.logger import setup_logger
    print('✓ 核心模块导入成功')
except ImportError as e:
    print(f'✗ 模块导入失败: {e}')
    sys.exit(1)
"
    
    # 检查ffmpeg
    if command_exists ffmpeg; then
        print_success "✓ ffmpeg 可用"
    else
        print_error "✗ ffmpeg 未正确安装"
        exit 1
    fi
    
    print_success "安装验证通过！"
}

# 创建启动脚本
create_startup_script() {
    print_info "创建启动脚本..."
    
    cat > run.sh << 'EOF'
#!/bin/bash
# ArXiv Video Downloader 启动脚本

cd "$(dirname "$0")"
source venv/bin/activate

echo "🚀 ArXiv Video Downloader"
echo "========================="
echo "使用默认配置启动..."
echo "如需自定义参数，请直接使用: python main.py --help"
echo ""

python main.py --workers 8
EOF

    chmod +x run.sh
    print_success "启动脚本创建完成: ./run.sh"
}

# 显示使用说明
show_usage() {
    echo ""
    echo "🎉 安装完成！"
    echo "============"
    echo ""
    echo "📁 项目目录: $(pwd)"
    echo ""
    echo "🚀 快速开始:"
    echo "   ./run.sh                    # 使用默认配置运行"
    echo "   source venv/bin/activate    # 激活虚拟环境"
    echo "   python main.py --help       # 查看所有选项"
    echo ""
    echo "📖 常用命令:"
    echo "   python main.py --workers 8                          # 8线程下载"
    echo "   python main.py --field cs.AI                        # 下载AI领域"
    echo "   python main.py --download-dir ~/Videos/arxiv        # 自定义目录"
    echo ""
    echo "📚 更多信息请查看 README.md"
    echo ""
}

# 主函数
main() {
    echo "🎬 ArXiv Video Downloader 自动安装程序"
    echo "======================================"
    echo ""
    
    # 检查root权限提醒
    if [[ $EUID -eq 0 ]]; then
        print_warning "检测到root权限，建议使用普通用户运行此脚本"
        read -p "是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    detect_os
    install_system_deps
    clone_project
    setup_python_env
    verify_installation
    create_startup_script
    show_usage
    
    print_success "🎉 安装完成！现在可以开始使用了！"
}

# 错误处理
trap 'print_error "安装过程中出现错误，请检查上面的错误信息"' ERR

# 运行主函数
main "$@"
