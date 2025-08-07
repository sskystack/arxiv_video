#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArXiv Video Downloader - 多线程版本
简化的启动脚本，支持多线程并发下载

使用方法：
python multi_thread_downloader.py
"""

import os
import sys
import threading
from datetime import datetime
import argparse  # 导入argparse

# 添加crawler路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'crawler'))
from multi_thread_arxiv_crawler import MultiThreadArxivCrawler

def print_banner():
    """打印欢迎横幅"""
    print("🚀 ArXiv Video Downloader - 多线程版本")
    print("=" * 60)
    print("✨ 特性:")
    print("  • 多线程并发下载，速度提升3-5倍")
    print("  • 智能任务分发，避免单点堵塞")
    print("  • 实时进度显示，了解下载状态")
    print("  • tqdm进度条显示下载详情")
    print("  • 日志自动记录到logs文件夹")
    print("  • 防反爬虫机制，安全稳定")
    print("=" * 60)

def get_user_input():
    """获取用户输入"""
    print("\n📋 配置下载参数:")
    
    # 获取下载目录
    default_dir = "/Users/zhouzhongtian/Movies/arxiv_video"
    download_dir_input = input(f"📁 下载目录 (默认: {default_dir}): ").strip()
    download_dir = download_dir_input if download_dir_input else default_dir
    print(f"✅ 设置下载目录: {download_dir}")
    
    # 获取线程数
    while True:
        try:
            threads_input = input("🔧 线程数量 (建议2-8，默认4): ").strip()
            max_workers = int(threads_input) if threads_input else 4
            max_workers = max(1, min(max_workers, 16))  # 限制在1-16之间
            break
        except ValueError:
            print("❌ 请输入有效的数字")
    
    print(f"✅ 设置线程数: {max_workers}")
    
    # 获取下载模式
    print("\n📅 选择下载模式:")
    print("1. 获取最新的N篇论文")
    print("2. 获取指定日期的论文")
    print("3. 获取最新发布日的所有论文")
    
    while True:
        choice = input("请选择模式 (1/2/3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("❌ 请输入 1、2 或 3")
    
    return max_workers, download_dir, choice

def run_mode_1(crawler):
    """模式1: 最新论文 - 使用网页抓取"""
    print("\n🔥 模式1: 下载最新论文 (网页抓取模式)")
    
    while True:
        try:
            papers_input = input("📄 要获取的论文数量 (建议5-50，默认25): ").strip()
            if papers_input == '':
                max_papers = 25
                break
            else:
                max_papers = int(papers_input)
                max_papers = max(1, max_papers)
                break
        except ValueError:
            print("❌ 请输入有效的数字")
    
    print(f"✅ 将抓取最新的 {max_papers} 篇CS.CV论文")
    
    # 直接调用新的网页抓取方法
    papers = crawler.get_recent_papers(field='cs.CV', max_papers=max_papers)
    
    if not papers:
        print("❌ 未能通过网页抓取到任何论文。")
        return []
        
    # 由于 get_recent_papers 直接返回论文信息，我们需要手动触发下载
    # 为了复用多线程下载逻辑，我们将其传递给一个通用的下载处理器
    return crawler.download_videos_for_papers(papers)

def run_mode_2(crawler):
    """模式2: 指定日期论文"""
    print("\n📅 模式2: 下载指定日期论文")
    
    while True:
        date_input = input("📅 输入日期 (YYYY-MM-DD 或 YYYYMMDD): ").strip()
        if len(date_input) in [8, 10]:
            break
        print("❌ 请输入正确的日期格式")
    
    while True:
        try:
            papers_input = input("📄 最大论文数量 (输入'all'下载全部，默认100): ").strip()
            
            if papers_input.lower() in ['all', '全部', 'a']:
                max_papers = 999999  # 设置足够大的数字
                print("✅ 将下载该日期的全部CS.CV论文")
                break
            elif papers_input == '':
                max_papers = 100
                break
            else:
                max_papers = int(papers_input)
                max_papers = max(1, max_papers)  # 移除上限限制
                break
        except ValueError:
            print("❌ 请输入有效的数字或'all'")
    
    if max_papers != 999999:
        print(f"✅ 将下载 {date_input} 的 {max_papers} 篇CS.CV论文")
    
    return crawler.crawl_videos_multi_thread(field='cs.CV', max_papers=max_papers, target_date=date_input)

def run_mode_3(crawler):
    """模式3: 最新发布日的所有论文"""
    print("\n🌟 模式3: 下载最新发布日的所有论文")
    
    print("📄 将自动查找最新发布日期并下载该日期的所有CS.CV论文")
    
    confirm = input("确认开始下载? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ 取消下载")
        return []
    
    return crawler.crawl_videos_for_latest_day(field='cs.CV', max_papers=1000)

def run_mode_id(crawler, paper_id):
    """模式ID: 下载指定ID的论文"""
    print(f"\n🆔 模式ID: 下载论文 {paper_id}")
    
    # 使用arxiv API获取单个论文的信息
    import arxiv
    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[paper_id])
        paper = next(client.results(search), None)
        
        if not paper:
            print(f"❌ 未能找到ID为 {paper_id} 的论文。")
            return []
            
        # 将 arxiv.Result 对象转换为我们内部使用的字典格式
        paper_info = {
            'id': paper.entry_id.split('/')[-1],
            'title': paper.title,
            'abstract_url': paper.entry_id,
            'authors': [author.name for author in paper.authors]
        }
        
        # 直接调用单个论文处理函数
        # 注意：process_single_paper 需要一个 target_date 参数用于创建文件夹
        # 在这里我们可以使用论文的发布日期
        target_date = paper.published.strftime("%Y%m%d")
        return [crawler.process_single_paper(paper_info, target_date=target_date)]

    except Exception as e:
        print(f"❌ 获取或处理论文 {paper_id} 时出错: {e}")
        return []

def print_results(results, target_date=None):
    """打印下载结果 - 增强版，兼容不同数据源"""
    print("\n" + "=" * 60)
    print("📊 下载结果统计")
    print("=" * 60)
    
    if not results:
        print("❌ 未找到可下载的视频")
        print("\n可能原因:")
        print("  • 该时间段没有CS.CV论文")
        print("  • 论文没有项目主页链接")
        print("  • 项目主页没有视频内容")
        print("  • 网络连接问题")
        return

    successful_papers = [res for res in results if res and res.get('videos')]
    
    print(f"✅ 成功下载了 {len(successful_papers)} 篇论文的视频")
    
    for result in successful_papers:
        paper_data = result['paper']
        videos = result['videos']
        
        # 兼容 arxiv.Result 对象和我们自己的字典
        is_dict = isinstance(paper_data, dict)
        
        paper_id = paper_data['id'] if is_dict else paper_data.entry_id.split('/')[-1]
        title = paper_data['title'] if is_dict else paper_data.title
        authors = paper_data['authors'] if is_dict else [author.name for author in paper_data.authors]
        
        print(f"\n📄 论文ID: {paper_id}")
        print(f"   标题: {title.strip()}")
        print(f"   作者: {', '.join(authors[:3])}")
        print(f"   视频数量: {len(videos)}")
        
        for i, video in enumerate(videos):
            local_path = video.get('local_path', 'N/A')
            print(f"     - 视频 {i+1}: {os.path.basename(local_path)}")

    # 打印下载文件夹路径
    if successful_papers:
        # 从第一个结果中获取下载文件夹路径
        first_video_path = successful_papers[0]['videos'][0].get('local_path')
        if first_video_path:
            # 路径通常是 /path/to/download/YYYYMMDD/paper_id/video.mp4
            # 我们需要获取到 /path/to/download
            download_folder = os.path.dirname(os.path.dirname(os.path.dirname(first_video_path)))
            print("\n" + "-" * 60)
            print(f"📂 所有视频已下载到: {download_folder}")
            print("-" * 60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ArXiv Video Downloader - 多线程版本")
    parser.add_argument('--workers', type=int, help="线程数 (1-16)")
    parser.add_argument('--mode', type=str, choices=['latest', 'date', 'latest_day', 'id'], help="运行模式: 'latest', 'date', 'latest_day', 'id'")
    parser.add_argument('--date', type=str, help="目标日期 (当模式为 'date' 时使用, 格式: YYYY-MM-DD 或 YYYYMMDD)")
    parser.add_argument('--max-papers', type=int, help="最大论文数")
    parser.add_argument('--paper-id', type=str, help="目标论文ID (当模式为 'id' 时使用)")
    parser.add_argument('--download-dir', type=str, help="下载目录路径 (默认: ~/Movies/arxiv_video)")
    
    args = parser.parse_args()

    # 如果通过命令行提供了参数，则直接运行
    try:
        if args.mode:  # 如果通过命令行参数指定了模式，则进入非交互模式
            max_workers = args.workers or 4
            download_dir = args.download_dir or "/Users/zhouzhongtian/Movies/arxiv_video"
            
            print(f"🔧 初始化多线程爬虫 (线程数: {max_workers})...")
            print(f"📁 下载目录: {download_dir}")
            crawler = MultiThreadArxivCrawler(download_folder=download_dir, max_workers=max_workers)
            
            import time
            start_time = time.time()
            
            print(f"\n🚀 开始下载...")
            print("=" * 60)
            
            results = []
            target_date_for_results = None
            
            if args.mode == 'latest':
                max_papers = args.max_papers if args.max_papers else 25
                papers = crawler.get_recent_papers(field='cs.CV', max_papers=max_papers)
                results = crawler.download_videos_for_papers(papers)
            elif args.mode == 'date':
                if not args.date:
                    print("❌ 错误: 使用 'date' 模式时必须提供 --date 参数。")
                    return
                max_papers = args.max_papers if args.max_papers else 100
                results = crawler.crawl_videos_multi_thread(field='cs.CV', max_papers=max_papers, target_date=args.date)
                target_date_for_results = args.date
            elif args.mode == 'latest_day':
                max_papers = args.max_papers if args.max_papers else 1000
                results = crawler.crawl_videos_for_latest_day(field='cs.CV', max_papers=max_papers)
                target_date_for_results = "最新发布日"
            elif args.mode == 'id':
                if not args.paper_id:
                    print("❌ 错误: 使用 'id' 模式时必须提供 --paper-id 参数。")
                    return
                results = run_mode_id(crawler, args.paper_id)

            elapsed_time = time.time() - start_time
            print_results(results, target_date_for_results)
            
            print(f"\n⏱️  总耗时: {elapsed_time:.1f} 秒")
            if results:
                avg_time = elapsed_time / len(results)
                print(f"📈 平均每篇论文: {avg_time:.1f} 秒")
            
            print("\n🎉 下载完成!")

        else:  # 否则，保持原有的交互模式
            # 打印横幅
            print_banner()
            
            # 获取用户输入
            max_workers, download_dir, choice = get_user_input()
            
            # 初始化爬虫
            print(f"\n🔧 初始化多线程爬虫 (线程数: {max_workers})...")
            print(f"📁 下载目录: {download_dir}")
            crawler = MultiThreadArxivCrawler(download_folder=download_dir, max_workers=max_workers)
            
            # 开始计时
            import time
            start_time = time.time()
            
            print(f"\n🚀 开始下载...")
            print("=" * 60)
            
            # 根据选择执行相应模式
            target_date_for_results = None
            if choice == '1':
                results = run_mode_1(crawler)
            elif choice == '2':
                results = run_mode_2(crawler)
                target_date_for_results = "指定日期"
            elif choice == '3':
                results = run_mode_3(crawler)
                target_date_for_results = "最新发布日"
            else:
                results = run_mode_1(crawler)  # 默认模式
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            
            # 打印结果
            print_results(results, target_date_for_results)
            
            print(f"\n⏱️  总耗时: {elapsed_time:.1f} 秒")
            if results:
                avg_time = elapsed_time / len(results)
                print(f"📈 平均每篇论文: {avg_time:.1f} 秒")
            
            print("\n🎉 下载完成!")
        
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断下载")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
    finally:
        try:
            crawler.close()
        except:
            pass

if __name__ == "__main__":
    main()
