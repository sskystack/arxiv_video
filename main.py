#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArXiv Video Downloader - 主入口文件
自动下载 ArXiv 论文项目页面视频的工具

使用方式:
    python main.py [--workers N] [--download-dir PATH] [--max-papers N] [--field FIELD]

示例:
    python main.py --workers 8 --download-dir ~/Videos/arxiv
    python main.py --max-papers 50 --field cs.CV
"""

import os
import sys
import argparse
from typing import Optional

from utils.logger import setup_logger, get_logger
from core.crawler import ArxivVideoCrawler


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='ArXiv Video Downloader - 下载最新一天的论文视频',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --workers 8                           # 使用8个线程
  %(prog)s --download-dir ~/Videos/arxiv         # 指定下载目录
  %(prog)s --max-papers 50                       # 最多下载50篇论文的视频
  %(prog)s --field cs.AI                         # 下载AI领域论文
        """
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=4,
        help='下载线程数 (默认: 4, 范围: 1-16)'
    )
    
    parser.add_argument(
        '--download-dir', '-d',
        type=str,
        default=os.path.expanduser('~/Movies/arxiv_video'),
        help='视频下载目录 (默认: ~/Movies/arxiv_video)'
    )
    
    parser.add_argument(
        '--max-papers', '-m',
        type=int,
        default=1000,
        help='最大论文数量 (默认: 1000)'
    )
    
    parser.add_argument(
        '--field', '-f',
        type=str,
        default='cs.CV',
        help='论文领域 (默认: cs.CV)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )
    
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> bool:
    """验证命令行参数"""
    # 验证线程数
    if not 1 <= args.workers <= 16:
        print(f"错误: 线程数必须在 1-16 之间，当前值: {args.workers}")
        return False
    
    # 验证最大论文数
    if args.max_papers <= 0:
        print(f"错误: 最大论文数必须大于0，当前值: {args.max_papers}")
        return False
    
    # 验证下载目录
    try:
        args.download_dir = os.path.abspath(os.path.expanduser(args.download_dir))
        os.makedirs(args.download_dir, exist_ok=True)
    except Exception as e:
        print(f"错误: 无法创建下载目录 {args.download_dir}: {e}")
        return False
    
    return True


def print_summary(results: list, args: argparse.Namespace) -> None:
    """打印下载结果摘要"""
    print("\n" + "="*60)
    print("📊 下载结果摘要")
    print("="*60)
    
    total_papers = len(results)
    total_videos = sum(len(result['videos']) for result in results)
    
    print(f"成功处理的论文数量: {total_papers}")
    print(f"总下载视频数量: {total_videos}")
    
    if results:
        print(f"视频保存目录: {args.download_dir}")
        print("\n📝 详细信息:")
        
        for i, result in enumerate(results, 1):
            paper = result['paper']
            videos = result['videos']
            
            print(f"\n{i}. 论文ID: {paper['id']}")
            print(f"   标题: {paper['title'][:80]}...")
            print(f"   作者: {', '.join(paper['authors'])}")
            if 'submitted_date' in paper:
                print(f"   提交日期: {paper['submitted_date']}")
            print(f"   视频数量: {len(videos)}")
            
            for j, video in enumerate(videos, 1):
                filename = os.path.basename(video['local_path'])
                print(f"     视频{j}: {filename}")
    else:
        print("\n❌ 未找到可下载的视频")
        print("\n可能的原因:")
        print("• 今天该领域没有论文发布")
        print("• 论文没有项目主页链接")
        print("• 项目主页没有视频内容")
        print("• 网络连接问题")


def main():
    """主函数"""
    # 解析和验证参数
    args = parse_arguments()
    
    if not validate_arguments(args):
        sys.exit(1)
    
    # 设置日志
    log_level = 10 if args.verbose else 20  # DEBUG if verbose else INFO
    logger = setup_logger('arxiv_crawler', log_level)
    
    # 打印启动信息
    print("🚀 ArXiv Video Downloader")
    print("="*50)
    print(f"论文领域: {args.field}")
    print(f"最大论文数: {args.max_papers}")
    print(f"下载线程数: {args.workers}")
    print(f"下载目录: {args.download_dir}")
    print("="*50)
    
    logger.info("ArXiv 视频下载器启动")
    logger.info(f"配置 - 领域: {args.field}, 线程数: {args.workers}, "
               f"最大论文数: {args.max_papers}, 下载目录: {args.download_dir}")
    
    crawler = None
    try:
        # 创建爬虫实例
        crawler = ArxivVideoCrawler(
            download_folder=args.download_dir,
            max_workers=args.workers
        )
        
        # 开始爬取
        results = crawler.crawl_latest_day_videos(
            field=args.field,
            max_papers=args.max_papers
        )
        
        # 打印结果摘要
        print_summary(results, args)
        
        logger.info("ArXiv 视频下载器完成")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断下载")
        logger.info("用户中断下载")
        
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        logger.error(f"程序执行出错: {e}", exc_info=True)
        sys.exit(1)
        
    finally:
        if crawler:
            crawler.close()


if __name__ == "__main__":
    main()