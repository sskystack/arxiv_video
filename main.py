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
  %(prog)s --publication-date 20250820           # 下载指定日期的论文
  %(prog)s --skip-existing                       # 跳过已存在res视频的论文
  %(prog)s --cookies-from-browser chrome         # 使用Chrome的Cookie下载YouTube视频
  %(prog)s -p 20250819 -w 8 -m 100 -s            # 组合使用参数
        """)
    
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
        '--publication-date', '-p',
        type=str,
        default=None,
        help='指定论文发布日期 (格式: YYYYMMDD，如: 20250820)。如不指定，自动获取最新日期'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细日志'
    )
    
    parser.add_argument(
        '--skip-existing', '-s',
        action='store_true',
        default=False,
        help='跳过已存在res视频的论文，不进行重复处理 (默认: False)'
    )

    parser.add_argument(
        '--cookies-from-browser',
        type=str,
        default=None,
        help='指定浏览器名称 (例如: chrome, firefox) 以加载cookie，用于需要登录的视频网站 (如YouTube)'
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
    
    # 验证发布日期格式
    if args.publication_date:
        if not _validate_date_format(args.publication_date):
            print(f"错误: 发布日期格式不正确，应为YYYYMMDD格式，当前值: {args.publication_date}")
            return False
    
    # 验证下载目录
    try:
        args.download_dir = os.path.abspath(os.path.expanduser(args.download_dir))
        os.makedirs(args.download_dir, exist_ok=True)
    except Exception as e:
        print(f"错误: 无法创建下载目录 {args.download_dir}: {e}")
        return False
    
    return True


def _validate_date_format(date_str: str) -> bool:
    """验证日期格式是否为YYYYMMDD"""
    try:
        if len(date_str) != 8:
            return False
        
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        
        # 基本范围检查
        if not (1900 <= year <= 2100):
            return False
        if not (1 <= month <= 12):
            return False
        if not (1 <= day <= 31):
            return False
        
        # 使用datetime进行更严格的验证
        from datetime import datetime
        datetime.strptime(date_str, '%Y%m%d')
        return True
        
    except (ValueError, TypeError):
        return False


def print_summary(results: list, args: argparse.Namespace) -> None:
    """打印下载结果摘要"""
    print("\n" + "="*60)
    print("📊 下载结果摘要")
    print("="*60)
    
    total_papers = len(results)
    cards_generated = sum(1 for result in results if result.get('has_script_card', False))
    composed_videos = sum(1 for result in results if result.get('composed_video_path'))
    
    print(f"成功处理的论文数量: {total_papers}")
    print(f"生成解说卡片数量: {cards_generated}")
    print(f"合成最终视频数量: {composed_videos}")
    
    if results:
        print(f"视频保存目录: {args.download_dir}")
        print(f"卡片保存目录: ./cards/")
        print("\n📝 详细信息:")
        
        for i, result in enumerate(results, 1):
            paper = result['paper']
            video = result.get('video')  # 现在是单个视频而不是数组
            arxiv_id = result.get('arxiv_id')
            has_card = result.get('has_script_card', False)
            composed_video = result.get('composed_video_path')
            
            print(f"\n{i}. 论文ID: {paper['id']}")
            print(f"   ArXiv ID: {arxiv_id or '未识别'}")
            print(f"   标题: {paper['title'][:80]}...")
            print(f"   作者: {', '.join(paper['authors'])}")
            if 'submitted_date' in paper:
                print(f"   提交日期: {paper['submitted_date']}")
            
            if video:
                print(f"   视频类型: {video.get('video_type', '未知')}")
                print(f"   解说卡片: {'✅ 已生成' if has_card else '❌ 未生成'}")
                print(f"   合成视频: {'✅ 已生成' if composed_video else '❌ 未生成'}")
                
                if composed_video:
                    composed_filename = os.path.basename(composed_video)
                    print(f"     最终视频: {composed_filename}")
                
                filename = os.path.basename(video['local_path'])
                print(f"     主视频: {filename}")
                print(f"     视频URL: {video['video_url']}")
            else:
                print(f"   视频: ❌ 未找到")
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
    if args.cookies_from_browser:
        print(f"Cookie来源: {args.cookies_from_browser}")
    print("="*50)
    
    logger.info("ArXiv 视频下载器启动")
    logger.info(f"配置 - 领域: {args.field}, 线程数: {args.workers}, "
               f"最大论文数: {args.max_papers}, 下载目录: {args.download_dir}, "
               f"跳过已存在视频: {args.skip_existing}, "
               f"Cookie来源: {args.cookies_from_browser}")
    
    if args.publication_date:
        logger.info(f"使用指定发布日期: {args.publication_date}")
    else:
        logger.info("将自动获取最新发布日期的论文")
    
    crawler = None
    try:
        # 创建爬虫实例
        crawler = ArxivVideoCrawler(
            download_folder=args.download_dir,
            max_workers=args.workers,
            skip_existing=args.skip_existing,
            cookies_from_browser=args.cookies_from_browser
        )
        
        # 开始爬取
        results = crawler.crawl_latest_day_videos(
            field=args.field,
            max_papers=args.max_papers,
            target_date=args.publication_date
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
