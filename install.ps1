# ArXiv Video Downloader Windows 自动安装脚本

# 设置错误处理
$ErrorActionPreference = "Stop"

# 颜色定义
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    switch ($Color) {
        "Red" { Write-Host $Message -ForegroundColor Red }
        "Green" { Write-Host $Message -ForegroundColor Green }
        "Yellow" { Write-Host $Message -ForegroundColor Yellow }
        "Blue" { Write-Host $Message -ForegroundColor Blue }
        default { Write-Host $Message }
    }
}

function Print-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Blue"
}

function Print-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" "Green"
}

function Print-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Print-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

# 检查是否以管理员权限运行
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 检查命令是否存在
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# 安装Chocolatey
function Install-Chocolatey {
    if (Test-Command "choco") {
        Print-Info "Chocolatey 已安装"
        return
    }
    
    Print-Info "安装 Chocolatey..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    
    # 刷新环境变量
    refreshenv
    Print-Success "Chocolatey 安装完成"
}

# 安装系统依赖
function Install-SystemDeps {
    Print-Info "安装系统依赖..."
    
    Install-Chocolatey
    
    # 检查并安装依赖
    $deps = @("python", "git", "ffmpeg")
    
    foreach ($dep in $deps) {
        if (Test-Command $dep) {
            Print-Info "$dep 已安装"
        } else {
            Print-Info "安装 $dep..."
            choco install $dep -y
        }
    }
    
    # 刷新环境变量
    refreshenv
    Print-Success "系统依赖安装完成"
}

# 克隆项目
function Clone-Project {
    Print-Info "克隆项目..."
    
    if (Test-Path "arxiv_video") {
        Print-Warning "项目目录已存在，更新项目..."
        Set-Location "arxiv_video"
        git pull origin main
    } else {
        git clone https://github.com/sskystack/arxiv_video.git
        Set-Location "arxiv_video"
    }
    
    Print-Success "项目代码准备完成"
}

# 设置Python环境
function Setup-PythonEnv {
    Print-Info "设置Python虚拟环境..."
    
    # 创建虚拟环境
    python -m venv venv
    
    # 激活虚拟环境
    & ".\venv\Scripts\Activate.ps1"
    
    # 升级pip
    python -m pip install --upgrade pip
    
    # 安装依赖
    Print-Info "安装Python依赖包..."
    pip install -r requirements.txt
    
    Print-Success "Python环境设置完成"
}

# 验证安装
function Test-Installation {
    Print-Info "验证安装..."
    
    # 激活虚拟环境
    & ".\venv\Scripts\Activate.ps1"
    
    # 测试导入主要模块
    $testScript = @"
import sys
sys.path.append('.')
try:
    from core.crawler import ArxivVideoCrawler
    from utils.logger import setup_logger
    print('✓ 核心模块导入成功')
except ImportError as e:
    print(f'✗ 模块导入失败: {e}')
    sys.exit(1)
"@
    
    python -c $testScript
    
    # 检查ffmpeg
    if (Test-Command "ffmpeg") {
        Print-Success "✓ ffmpeg 可用"
    } else {
        Print-Error "✗ ffmpeg 未正确安装"
        exit 1
    }
    
    Print-Success "安装验证通过！"
}

# 创建启动脚本
function New-StartupScript {
    Print-Info "创建启动脚本..."
    
    $scriptContent = @"
@echo off
REM ArXiv Video Downloader 启动脚本

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo 🚀 ArXiv Video Downloader
echo =========================
echo 使用默认配置启动...
echo 如需自定义参数，请直接使用: python main.py --help
echo.

python main.py --workers 8
pause
"@

    Set-Content -Path "run.bat" -Value $scriptContent -Encoding UTF8
    Print-Success "启动脚本创建完成: run.bat"
}

# 显示使用说明
function Show-Usage {
    Write-Host ""
    Write-ColorOutput "🎉 安装完成！" "Green"
    Write-Host "============"
    Write-Host ""
    Write-Host "📁 项目目录: $(Get-Location)"
    Write-Host ""
    Write-ColorOutput "🚀 快速开始:" "Blue"
    Write-Host "   .\run.bat                       # 使用默认配置运行"
    Write-Host "   .\venv\Scripts\Activate.ps1     # 激活虚拟环境"
    Write-Host "   python main.py --help           # 查看所有选项"
    Write-Host ""
    Write-ColorOutput "📖 常用命令:" "Blue"
    Write-Host "   python main.py --workers 8                          # 8线程下载"
    Write-Host "   python main.py --field cs.AI                        # 下载AI领域"
    Write-Host "   python main.py --download-dir C:\Videos\arxiv       # 自定义目录"
    Write-Host ""
    Write-Host "📚 更多信息请查看 README.md"
    Write-Host ""
}

# 主函数
function Main {
    Write-ColorOutput "🎬 ArXiv Video Downloader 自动安装程序" "Blue"
    Write-Host "======================================"
    Write-Host ""
    
    # 检查管理员权限
    if (-not (Test-Administrator)) {
        Print-Error "此脚本需要管理员权限才能安装系统依赖"
        Print-Info "请右键选择 '以管理员身份运行 PowerShell' 后重新执行此脚本"
        exit 1
    }
    
    try {
        Install-SystemDeps
        Clone-Project
        Setup-PythonEnv
        Test-Installation
        New-StartupScript
        Show-Usage
        
        Print-Success "🎉 安装完成！现在可以开始使用了！"
    }
    catch {
        Print-Error "安装过程中出现错误: $($_.Exception.Message)"
        exit 1
    }
}

# 运行主函数
Main
