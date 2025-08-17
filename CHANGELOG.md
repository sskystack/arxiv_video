# 变更日志

本文档记录了项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增
- 完整的README文档，包含详细的安装和使用指南
- 自动安装脚本（Linux/macOS/Windows）
- 快速启动脚本
- GitHub Issue和PR模板
- 贡献指南文档

### 修复
- 修复了重复下载同一论文视频的问题
- 优化了错误处理和日志记录

### 变更
- 重构了项目架构，采用模块化设计
- 改进了命令行界面，使用argparse
- 优化了多线程下载逻辑

## [1.0.0] - 2024-XX-XX

### 新增
- 初始版本发布
- 多线程ArXiv论文视频下载功能
- 支持YouTube、Bilibili等视频平台
- 实时下载进度显示
- 按日期和论文ID组织文件
- 详细的日志记录系统

[Unreleased]: https://github.com/sskystack/arxiv_video/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/sskystack/arxiv_video/releases/tag/v1.0.0
