#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArXiv Video Crawler - 多线程增强版本
专门用于爬取arXiv CS.CV论文的演示视频，支持多线程并发下载

特性：
- 多线程并发处理论文
- 智能任务分发
- 日志记录到logs文件夹
- 进度条显示
- 防反爬虫机制
- 错误重试机制
"""

import os
import re
import time
import random
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
from queue import Queue
import sys
import yt_dlp
from tqdm import tqdm

# 配置日志到logs文件夹
def setup_logger():
    """设置日志配置"""
    # 创建logs目录
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger('multi_thread_arxiv_crawler')
    logger.setLevel(logging.INFO)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建文件处理器
    log_filename = f"multi_thread_crawler_{datetime.now().strftime('%Y_%m_%d')}.log"
    log_filepath = os.path.join(logs_dir, log_filename)
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 初始化日志
logger = setup_logger()

# User-Agent列表
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.123 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:88.0) Gecko/20100101 Firefox/88.0',
]

class ThreadSafeCounter:
    """线程安全的计数器"""
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()
    
    def increment(self):
        with self._lock:
            self._value += 1
            return self._value
    
    @property
    def value(self):
        with self._lock:
            return self._value

class MultiThreadArxivCrawler:
    def __init__(self, download_folder="/Users/zhouzhongtian/Movies/arxiv_video", max_workers=4):
        self.download_folder = download_folder
        self.max_workers = max_workers
        self.session_pool = []
        self.results = []
        self.results_lock = threading.Lock()
        self.progress_counter = ThreadSafeCounter()
        self.success_counter = ThreadSafeCounter()
        self.error_counter = ThreadSafeCounter()
        self._setup()
    
    def _setup(self):
        """初始化设置"""
        # 创建下载目录
        os.makedirs(self.download_folder, exist_ok=True)
        
        # 初始化requests session池
        try:
            import requests
            for i in range(self.max_workers):
                session = requests.Session()
                session.headers.update({
                    'User-Agent': random.choice(USER_AGENTS)
                })
                self.session_pool.append(session)
            logger.info(f"初始化了 {len(self.session_pool)} 个HTTP会话")
        except ImportError:
            logger.error("请安装 requests: pip install requests")
            return False
        
        return True
    
    def _get_session(self):
        """获取一个session（线程安全）"""
        return random.choice(self.session_pool)
    
    def get_papers_by_date(self, field='cs.CV', target_date=None, max_papers=1000):
        """获取指定日期的论文列表 - 改进版本，确保完整性"""
        if target_date is None:
            target_date = datetime.now().strftime("%Y%m%d")
        elif isinstance(target_date, str):
            # 如果是字符串，确保格式正确
            if len(target_date) == 8:  # YYYYMMDD格式
                target_date = target_date
            elif len(target_date) == 10:  # YYYY-MM-DD格式
                target_date = target_date.replace('-', '')
            else:
                target_date = datetime.now().strftime("%Y%m%d")
        
        logger.info(f"开始获取 {field} 领域在 {target_date} 日期的论文")
        
        try:
            import arxiv
            # from arxiv.exceptions import UnexpectedEmptyPageError # 已修正：此导入方式不正确
            
            # 计算目标日期的前一天和后一天，用于完整性检查
            target_date_obj = datetime.strptime(target_date, "%Y%m%d")
            prev_date = (target_date_obj - timedelta(days=1)).strftime("%Y%m%d")
            next_date = (target_date_obj + timedelta(days=1)).strftime("%Y%m%d")
            
            client = arxiv.Client()
            papers = []
            seen_dates = set()  # 记录已经看到的日期
            processed_ids = set()  # 记录已处理的论文ID，避免重复
            
            # 使用更大的搜索范围来确保完整性
            search_size = max(max_papers * 10, 2000)  # 至少搜索2000篇论文
            
            logger.info(f"目标日期: {target_date}, 前一天: {prev_date}, 后一天: {next_date}")
            logger.info(f"将搜索最多 {search_size} 篇最新论文以确保完整性")
            
            # 创建搜索请求
            search = arxiv.Search(
                query=f"cat:{field}",
                max_results=search_size,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            try:
                paper_count = 0
                target_date_papers = 0
                
                for result in client.results(search):
                    paper_count += 1
                    paper_id = result.entry_id.split('/')[-1]
                    
                    # 避免重复处理
                    if paper_id in processed_ids:
                        continue
                    processed_ids.add(paper_id)
                    
                    submitted_date = result.published.strftime("%Y%m%d")
                    seen_dates.add(submitted_date)
                    
                    # 只保留目标日期的论文
                    if submitted_date == target_date:
                        paper_info = {
                            'id': paper_id,
                            'title': result.title.strip(),
                            'abstract_url': f"https://arxiv.org/abs/{paper_id}",
                            'authors': [author.name for author in result.authors[:3]],
                            'submitted_date': submitted_date,
                            'published_date': result.published.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        papers.append(paper_info)
                        target_date_papers += 1
                        logger.debug(f"找到目标日期论文: {paper_id}")
                        
                        # 如果已经找到足够多的目标日期论文，可以考虑停止
                        if len(papers) >= max_papers:
                            logger.info(f"已找到足够多的目标日期论文: {len(papers)} 篇")
                            break
                    
                    # 每处理100篇论文输出一次进度
                    if paper_count % 100 == 0:
                        logger.info(f"已处理 {paper_count} 篇论文，"
                                  f"目标日期论文: {target_date_papers} 篇，"
                                  f"已见日期范围: {min(seen_dates) if seen_dates else 'N/A'} - {max(seen_dates) if seen_dates else 'N/A'}")
                    
                    # 完整性检查：如果我们已经看到了目标日期的前一天，说明已经搜索得足够深入
                    if prev_date in seen_dates and target_date_papers > 0:
                        logger.info("完整性检查: 已找到前一天的论文，认为搜索完整")
                        break
                    
                    # 如果搜索到的最早日期比目标日期早太多（超过7天），且没有找到目标日期论文
                    earliest_date = min(seen_dates) if seen_dates else target_date
                    if earliest_date < prev_date and target_date_papers == 0:
                        days_diff = (datetime.strptime(target_date, "%Y%m%d") - 
                                   datetime.strptime(earliest_date, "%Y%m%d")).days
                        if days_diff > 7:  # 如果搜索超过7天前还没找到，可能确实没有
                            logger.info(f"已搜索到 {days_diff} 天前的论文，认为目标日期确实没有论文")
                            break
                
                # 最终结果报告
                logger.info(f"搜索完成: 总共处理 {paper_count} 篇论文")
                logger.info(f"找到 {len(papers)} 篇 {target_date} 日期的论文")
                logger.info(f"搜索过程中见到的日期范围: {min(seen_dates) if seen_dates else 'N/A'} - {max(seen_dates) if seen_dates else 'N/A'}")
                
                if len(papers) == 0:
                    logger.warning(f"警告: 未找到 {target_date} 日期的任何 {field} 论文")
                    logger.info("可能的原因:")
                    logger.info("1. 该日期确实没有该领域的论文发布")
                    logger.info("2. 论文发布日期可能与您查询的日期不同")
                    logger.info("3. 该日期可能是周末或节假日，通常论文较少")
                    if seen_dates:
                        closest_dates = sorted([d for d in seen_dates if abs(
                            (datetime.strptime(d, "%Y%m%d") - target_date_obj).days) <= 3])
                        if closest_dates:
                            logger.info(f"附近有论文的日期: {closest_dates}")
                
                return papers
            
            except arxiv.UnexpectedEmptyPageError:
                logger.info("Arxiv API返回空页面，这通常意味着已到达结果末尾，将正常结束搜索。")
                # This is not a critical error, just the end of results. We can proceed.
                return papers # 返回已获取的论文
            except Exception as search_error:
                logger.error(f"搜索过程中发生未知错误: {search_error}")
                return papers  # 返回已获取的论文
            
        except Exception as e:
            logger.error(f"获取 {target_date} 日期论文失败: {e}")
            return []
    
    def get_recent_papers(self, field='cs.CV', max_papers=25):
        """获取最新论文列表 - 使用网页抓取"""
        logger.info(f"开始通过网页抓取 {field} 领域的 {max_papers} 篇最新论文")
        
        # 使用 skip 和 show 参数，明确指定从头开始获取
        url = f'https://arxiv.org/list/{field}/recent?skip=0&show={max_papers}'
        
        try:
            from bs4 import BeautifulSoup
            
            session = self._get_session()
            response = session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            papers = []
            dl_content = soup.find('dl')
            if not dl_content:
                logger.warning(f"在页面 {url} 上没有找到论文列表 (<dl> 标签)")
                return []

            # 提取所有的 <dt> 和 <dd> 标签对
            dt_tags = dl_content.find_all('dt')
            dd_tags = dl_content.find_all('dd')

            if len(dt_tags) != len(dd_tags):
                logger.error(f"解析页面时发现dt/dd数量不匹配 ({len(dt_tags)}!={len(dd_tags)})，页面结构可能已更改。")
                return []

            for i in range(len(dt_tags)):
                dt = dt_tags[i]
                dd = dd_tags[i]

                # 从 <dt> 中提取论文ID
                id_tag = dt.find('a', title='Abstract')
                if not id_tag: continue
                paper_id = id_tag.text.replace('arXiv:', '').strip()

                # 从 <dd> 中提取标题
                title_div = dd.find('div', class_='list-title')
                if not title_div: continue
                title = title_div.text.replace('Title:', '').strip()

                # 从 <dd> 中提取作者
                authors_div = dd.find('div', class_='list-authors')
                if not authors_div: continue
                author_list = [a.text.strip() for a in authors_div.find_all('a')]

                paper_info = {
                    'id': paper_id,
                    'title': title,
                    'abstract_url': f"https://arxiv.org/abs/{paper_id}",
                    'authors': author_list[:3]  # 只取前3个作者
                }
                papers.append(paper_info)
                logger.info(f"找到论文: {paper_info['id']} - {paper_info['title'][:50]}...")

            logger.info(f"总共获取到 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"通过网页抓取获取论文失败: {e}")
            return []
    
    def download_videos_for_papers(self, papers):
        """
        为给定的论文信息列表（字典格式）下载视频。
        这是为网页抓取模式设计的通用下载处理器。
        """
        if not papers:
            logger.info("没有提供任何论文进行下载。")
            return []

        logger.info(f"准备为 {len(papers)} 篇论文启动多线程下载...")
        
        self.results = []
        self.progress_counter = ThreadSafeCounter()
        self.success_counter = ThreadSafeCounter()
        self.error_counter = ThreadSafeCounter()
        total_papers = len(papers)

        # 创建整体进度条
        overall_progress = tqdm(
            total=total_papers,
            desc="处理论文",
            unit="篇",
            position=0,
            leave=True
        )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 创建任务队列
            future_to_paper = {
                executor.submit(self.process_single_paper, paper): paper
                for paper in papers
            }
            
            # 等待任务完成
            for future in as_completed(future_to_paper):
                try:
                    result = future.result()
                    if result:
                        with self.results_lock:
                            self.results.append(result)
                        overall_progress.set_description(f"处理论文 (成功: {len(self.results)})")
                    
                    # 更新整体进度
                    overall_progress.update(1)
                    
                except Exception as e:
                    paper = future_to_paper[future]
                    paper_id = paper.get('id', 'N/A')
                    logger.error(f"处理论文 {paper_id} 时发生致命错误: {e}", exc_info=True)
                    overall_progress.update(1)

        overall_progress.close()
        return self.results

    def extract_project_links(self, abstract_url, session):
        """从arXiv摘要页面提取项目链接"""
        logger.debug(f"提取项目链接: {abstract_url}")
        
        try:
            import requests
            # 随机延迟 - 优化为更短的延迟
            time.sleep(random.uniform(0.2, 1.0))  # 减少延迟时间
            
            response = session.get(abstract_url, timeout=10)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 定义黑名单链接（需要过滤掉的链接）
            blacklist_urls = [
                'https://info.arxiv.org/help',
                'https://arxiv.org/help',
                'https://info.arxiv.org',
                'https://arxiv.org/abs',
                'https://arxiv.org/pdf',
                'https://arxiv.org/format',
                'https://arxiv.org/e-print',
                'mailto:',
                'javascript:',
                '#'
            ]
            
            # 查找项目链接
            project_links = []
            
            # 方法1: 查找外部链接
            external_links = soup.find_all('a', href=True)
            for link in external_links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                # 首先检查是否在黑名单中
                if any(blacklist in href for blacklist in blacklist_urls):
                    logger.debug(f"过滤黑名单链接: {href}")
                    continue
                
                # 判断是否为项目页面链接
                if any(keyword in href for keyword in ['github.io', 'project', 'demo', 'page']):
                    if href.startswith('http'):
                        project_links.append(href)
                        logger.debug(f"找到项目链接: {href}")
                
                # 也检查链接文本
                elif any(keyword in text for keyword in ['project', 'demo', 'page', 'website']):
                    if href.startswith('http'):
                        # 再次检查黑名单（确保万无一失）
                        if not any(blacklist in href for blacklist in blacklist_urls):
                            project_links.append(href)
                            logger.debug(f"找到项目链接(通过文本): {href}")
            
            return list(set(project_links))  # 去重
            
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 404:
                logger.warning(f"项目链接无法访问 (404 Not Found): {abstract_url}")
            else:
                logger.error(f"提取项目链接时发生HTTP错误: {http_err}")
            return []
        except Exception as e:
            logger.error(f"提取项目链接失败: {e}")
            return []

    def _convert_bilibili_url(self, url):
        """将Bilibili嵌入式URL转换为标准视频URL"""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        bvid = query_params.get('bvid', [None])[0]
        if bvid:
            return f"https://www.bilibili.com/video/{bvid}"
            
        aid = query_params.get('aid', [None])[0]
        if aid:
            return f"https://www.bilibili.com/video/av{aid}"
            
        return url # 如果无法转换，返回原URL

    def extract_video_urls(self, project_url, session):
        """提取视频URL"""
        logger.debug(f"提取视频URL: {project_url}")
        
        try:
            import requests
            # 随机延迟 - 优化为更短的延迟
            time.sleep(random.uniform(0.5, 1.5))  # 减少延迟时间
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = session.get(project_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- 智能URL拼接 ---
            # 1. 检查是否存在 <base> 标签，它会改变所有相对链接的基准
            base_tag = soup.find('base', href=True)
            base_url = base_tag['href'] if base_tag else project_url
            # 确保基准URL以 / 结尾，以便 urljoin 正确工作
            if not base_url.endswith('/'):
                base_url += '/'
            
            logger.debug(f"使用的基准URL进行拼接: {base_url}")

            video_urls = []
            
            # 查找video标签
            videos = soup.find_all('video')
            for video in videos:
                # 优先使用 video 标签的 src 属性
                src = video.get('src')
                if src:
                    full_url = urljoin(base_url, src)
                    video_urls.append(full_url)
                    logger.debug(f"找到 <video> 标签中的视频 URL: {full_url}")
                
                # 其次查找内部的 source 标签
                sources = video.find_all('source')
                for source in sources:
                    src = source.get('src')
                    if src:
                        full_url = urljoin(base_url, src)
                        video_urls.append(full_url)
                        logger.debug(f"找到 <source> 标签中的视频 URL: {full_url}")
            
            # 新增：查找iframe中的视频
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src')
                if src:
                    # 检查是否是YouTube或Bilibili的嵌入链接
                    if 'youtube.com/embed/' in src:
                        # YouTube链接通常是完整的，但以防万一
                        full_url = urljoin(base_url, src)
                        video_urls.append(full_url)
                        logger.debug(f"找到嵌入的YouTube视频链接: {full_url}")
                    
                    elif 'player.bilibili.com' in src:
                        # Bilibili链接需要特殊转换
                        converted_url = self._convert_bilibili_url(src)
                        video_urls.append(converted_url)
                        logger.debug(f"找到并转换Bilibili链接: {src} -> {converted_url}")

            # 也查找直接指向视频文件的链接
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if href and href.lower().endswith(('.mp4', '.webm', '.avi', '.mov')):
                    # 使用我们确定的基准URL进行拼接
                    full_url = urljoin(base_url, href)
                    video_urls.append(full_url)
                    logger.debug(f"找到 <a> 标签中的视频链接: {full_url}")
            
            return list(set(video_urls))  # 去重
            
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 404:
                logger.warning(f"项目页面无法访问 (404 Not Found): {project_url}")
            else:
                logger.error(f"访问项目页面时发生HTTP错误: {http_err}")
            return []
        except Exception as e:
            logger.error(f"提取视频URL失败: {e}")
            return []
    
    def download_video(self, video_url, paper_id, video_index, session, target_date=None, max_retries=3):
        """下载视频文件，支持断点重试、智能错误处理，并使用yt-dlp处理视频网站"""
        logger.debug(f"开始处理下载: {video_url}")

        # 确定文件路径
        if target_date:
            date_folder_name = target_date.replace('-', '') if len(target_date) == 10 else target_date
        else:
            date_folder_name = datetime.now().strftime("%Y%m%d")
        
        date_folder = os.path.join(self.download_folder, date_folder_name)
        paper_folder = os.path.join(date_folder, paper_id)
        os.makedirs(paper_folder, exist_ok=True)
        
        # --- 使用 yt-dlp 下载 ---
        if 'youtube.com' in video_url or 'bilibili.com' in video_url:
            logger.info(f"检测到视频网站链接，使用 yt-dlp 下载: {video_url}")
            try:
                # 创建一个自定义的进度钩子函数
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        try:
                            # 获取下载进度信息
                            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                            downloaded_bytes = d.get('downloaded_bytes', 0)
                            
                            if total_bytes > 0 and not hasattr(progress_hook, 'pbar'):
                                # 创建进度条（只创建一次）
                                progress_hook.pbar = tqdm(
                                    total=total_bytes,
                                    unit='B',
                                    unit_scale=True,
                                    desc=f"yt-dlp下载 video_{video_index}",
                                    leave=False
                                )
                                progress_hook.last_downloaded = 0
                            
                            if hasattr(progress_hook, 'pbar') and total_bytes > 0:
                                # 更新进度条
                                increment = downloaded_bytes - progress_hook.last_downloaded
                                if increment > 0:
                                    progress_hook.pbar.update(increment)
                                    progress_hook.last_downloaded = downloaded_bytes
                                
                        except Exception:
                            pass  # 忽略进度条错误，不影响下载
                    
                    elif d['status'] == 'finished':
                        if hasattr(progress_hook, 'pbar'):
                            progress_hook.pbar.close()
                            delattr(progress_hook, 'pbar')

                # 设置yt-dlp选项，优先下载1080p或更高分辨率的mp4
                ydl_opts = {
                    'format': 'bestvideo[height>=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': os.path.join(paper_folder, f"video_{video_index}.%(ext)s"), # 文件名模板
                    'noplaylist': True, # 如果是播放列表，只下载单个视频
                    'quiet': False, # 允许显示一些输出
                    'no_warnings': True, # 但不显示警告
                    'merge_output_format': 'mp4',
                    'progress_hooks': [progress_hook],  # 添加进度钩子
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }],
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                
                # yt-dlp不直接返回文件名，我们需要自己推断
                # 这里假设下载成功后文件名为 video_{video_index}.mp4
                filepath = os.path.join(paper_folder, f"video_{video_index}.mp4")
                if os.path.exists(filepath):
                     logger.info(f"yt-dlp 下载成功: {filepath}")
                     return filepath
                else: # 尝试其他可能的扩展名
                    for ext in ['mkv', 'webm']:
                        filepath = os.path.join(paper_folder, f"video_{video_index}.{ext}")
                        if os.path.exists(filepath):
                            logger.info(f"yt-dlp 下载成功: {filepath}")
                            return filepath
                logger.warning(f"yt-dlp 下载后未找到文件，URL: {video_url}")
                return None

            except Exception as e:
                logger.error(f"使用 yt-dlp 下载失败: {e}")
                return None
        
        # --- 原有的 requests 下载逻辑 ---
        logger.debug(f"使用 requests 下载: {video_url}")
        for retry in range(max_retries):
            start_time = time.time()
            
            try:
                headers = {
                    'User-Agent': random.choice(USER_AGENTS),
                    'Accept': 'video/mp4,video/*;q=0.9,*/*;q=0.8',
                    'Referer': video_url.split('/')[0] + '//' + video_url.split('/')[2],
                }
                
                response = session.get(video_url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()
                
                file_size = int(response.headers.get('content-length', 0))
                if file_size > 500 * 1024 * 1024: # 限制提高到500MB
                    logger.warning(f"视频文件过大 ({file_size/1024/1024:.1f}MB)，跳过下载")
                    return None
                
                content_type = response.headers.get('content-type', '').lower()
                if 'mp4' in content_type:
                    ext = '.mp4'
                elif 'webm' in content_type:
                    ext = '.webm'
                elif video_url.lower().endswith('.mp4'):
                    ext = '.mp4'
                elif video_url.lower().endswith('.webm'):
                    ext = '.webm'
                else:
                    ext = '.mp4'
                
                filename = f"video_{video_index}{ext}"
                filepath = os.path.join(paper_folder, filename)
                
                # 使用tqdm显示下载进度
                downloaded_bytes = 0
                with open(filepath, 'wb') as f:
                    # 创建进度条
                    progress_bar = tqdm(
                        total=file_size,
                        unit='B',
                        unit_scale=True,
                        desc=f"下载 video_{video_index}{ext}",
                        leave=False,
                        miniters=1
                    )
                    
                    try:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded_bytes += len(chunk)
                                progress_bar.update(len(chunk))
                    finally:
                        progress_bar.close()
                
                download_time = time.time() - start_time
                file_size_mb = downloaded_bytes / (1024 * 1024)
                avg_speed_kbps = (downloaded_bytes / 1024) / download_time if download_time > 0 else 0
                
                logger.info(f"视频下载成功: {filepath}")
                logger.info(f"下载统计: {filename} | {file_size_mb:.1f}MB | {download_time:.1f}s | 平均速率: {avg_speed_kbps:.1f}KB/s")
                
                return filepath
                
            except Exception as e:
                download_time = time.time() - start_time
                if retry < max_retries - 1:
                    logger.warning(f"下载失败 (重试 {retry+1}/{max_retries}): {e}")
                    time.sleep(random.uniform(2, 5))
                else:
                    logger.error(f"下载视频最终失败 ({download_time:.1f}s): {e}")
                    return None
        
        return None
    
    def process_single_paper(self, paper, target_date=None):
        """处理单个论文（线程执行函数）"""
        thread_id = threading.current_thread().ident
        
        # 兼容 arxiv.Result 对象和我们自己的字典
        is_dict = isinstance(paper, dict)
        
        paper_id = paper['id'] if is_dict else paper.entry_id.split('/')[-1]
        title = paper['title'] if is_dict else paper.title
        abstract_url = paper['abstract_url'] if is_dict else paper.entry_id
        
        # 统一日志输出
        logger.info(f"[{thread_id}] 开始处理论文: {paper_id} - {title[:60]}...")
        
        session = self._get_session()
        
        try:
            # 更新进度
            current_progress = self.progress_counter.increment()
            
            # 1. 提取项目链接
            project_links = self.extract_project_links(abstract_url, session)
            
            if not project_links:
                logger.info(f"[线程{thread_id}] 论文 {paper_id} 没有找到项目链接")
                return None
            
            paper_videos = []
            
            # 2. 从项目页面提取视频
            for project_url in project_links:
                logger.info(f"[线程{thread_id}] 检查项目页面: {project_url}")
                
                video_urls = self.extract_video_urls(project_url, session)
                
                if not video_urls:
                    logger.debug(f"[线程{thread_id}] 项目页面 {project_url} 没有找到视频")
                    continue
                
                # 3. 下载视频，传递目标日期参数
                for j, video_url in enumerate(video_urls):
                    time.sleep(random.uniform(0.2, 1.0))  # 进一步减少延迟
                    
                    downloaded_path = self.download_video(video_url, paper_id, j, session, target_date)
                    if downloaded_path:
                        paper_videos.append({
                            'video_url': video_url,
                            'local_path': downloaded_path,
                            'project_url': project_url
                        })
            
            if paper_videos:
                result = {
                    'paper': paper,
                    'videos': paper_videos
                }
                
                # 注意：不在这里添加到 self.results，由调用方负责添加
                # 这样避免重复添加到结果列表中
                
                self.success_counter.increment()
                logger.info(f"[线程{thread_id}] 论文 {paper_id} 成功下载 {len(paper_videos)} 个视频")
                return result
            else:
                logger.info(f"[线程{thread_id}] 论文 {paper_id} 没有找到可下载的视频")
                return None
                
        except Exception as e:
            self.error_counter.increment()
            logger.error(f"[线程{thread_id}] 处理论文 {paper_id} 时出错: {e}")
            return None
    
    def crawl_videos_multi_thread(self, field='cs.CV', max_papers=10, target_date=None):
        """多线程爬取视频"""
        if target_date:
            logger.info(f"开始多线程爬取 {field} 领域在 {target_date} 日期的论文视频")
            papers = self.get_papers_by_date(field, target_date, max_papers)
        else:
            logger.info(f"开始多线程爬取 {field} 领域的论文视频")
            papers = self.get_recent_papers(field, max_papers)
            
        if not papers:
            logger.error("未获取到论文列表")
            return []
        
        logger.info(f"将使用 {self.max_workers} 个线程处理 {len(papers)} 篇论文")
        
        # 重置计数器
        self.progress_counter = ThreadSafeCounter()
        self.success_counter = ThreadSafeCounter()
        self.error_counter = ThreadSafeCounter()
        self.results = []
        
        # 使用线程池执行
        start_time = time.time()
        
        # 创建整体进度条
        overall_progress = tqdm(
            total=len(papers),
            desc="处理论文",
            unit="篇",
            position=0,
            leave=True
        )
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务，传递目标日期参数
            future_to_paper = {executor.submit(self.process_single_paper, paper, target_date): paper for paper in papers}
            
            # 处理完成的任务
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                try:
                    result = future.result()
                    if result:
                        with self.results_lock:
                            self.results.append(result)
                    
                    # 更新进度条
                    success = len(self.results)
                    overall_progress.set_description(f"处理论文 (成功: {success})")
                    overall_progress.update(1)
                    
                except Exception as exc:
                    logger.error(f"论文 {paper['id']} 处理异常: {exc}")
                    overall_progress.update(1)
        
        overall_progress.close()
        
        elapsed_time = time.time() - start_time
        logger.info(f"多线程爬取完成！总耗时: {elapsed_time:.1f}s")
        logger.info(f"成功处理 {len(self.results)} 篇论文，成功率: {len(self.results)/len(papers)*100:.1f}%")
        
        return self.results

    def crawl_videos_for_latest_day(self, field='cs.CV', max_papers=1000):
        """
        获取最新发布日的所有论文视频。
        首先找到最新的发布日期，然后获取该日期的所有论文进行处理。
        """
        logger.info(f"开始查找 {field} 领域的最新发布日期...")
        try:
            import arxiv
            client = arxiv.Client()
            # 查找最新的一篇论文来确定日期
            search = arxiv.Search(
                query=f"cat:{field}",
                max_results=1,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            # 使用 next() 安全地获取第一个结果
            iterator = client.results(search)
            latest_paper = next(iterator, None)
            
            if not latest_paper:
                logger.warning("未能找到任何论文来确定最新日期。")
                return []
                
            latest_date = latest_paper.published.strftime("%Y%m%d")
            logger.info(f"找到最新发布日期为: {latest_date}，开始获取该日期的所有论文...")
            
            # 直接调用现有的多线程处理方法
            return self.crawl_videos_multi_thread(field=field, max_papers=max_papers, target_date=latest_date)

        except Exception as e:
            logger.error(f"获取最新日期论文时出错: {e}")
            return []
    
    def close(self):
        """清理资源"""
        for session in self.session_pool:
            session.close()

def main():
    """主函数"""
    print("ArXiv Video Crawler - 多线程增强版本")
    print("=" * 50)
    
    # 询问线程数
    try:
        max_workers = int(input("请输入线程数 (建议2-8，默认4): ").strip() or "4")
        max_workers = max(1, min(max_workers, 16))  # 限制在1-16之间
    except ValueError:
        max_workers = 4
    
    crawler = MultiThreadArxivCrawler(max_workers=max_workers)
    
    try:
        # 选择爬取模式
        print("\n请选择爬取模式：")
        print("1. 获取最新论文")
        print("2. 获取指定日期的论文")
        print("3. 获取今天的所有论文")
        
        choice = input("请输入选择 (1/2/3): ").strip()
        
        if choice == "1":
            max_papers = int(input("最大论文数量 (默认10): ").strip() or "10")
            results = crawler.crawl_videos_multi_thread(field='cs.CV', max_papers=max_papers)
            
        elif choice == "2":
            date_input = input("请输入日期 (格式: YYYY-MM-DD 或 YYYYMMDD): ").strip()
            max_papers = input("最大论文数量 (默认100): ").strip()
            max_papers = int(max_papers) if max_papers else 100
            
            results = crawler.crawl_videos_multi_thread(field='cs.CV', max_papers=max_papers, target_date=date_input)
            
        elif choice == "3":
            # 获取今天的所有CS.CV论文
            today = datetime.now().strftime("%Y%m%d")
            print(f"获取今天 ({today}) 的所有CS.CV论文...")
            results = crawler.crawl_videos_multi_thread(field='cs.CV', max_papers=1000, target_date=today)
            
        else:
            print("无效选择，使用默认模式...")
            results = crawler.crawl_videos_multi_thread(field='cs.CV', max_papers=10)
        
        # 打印结果
        print(f"\n=== 爬取结果 ===")
        print(f"成功处理的论文数量: {len(results)}")
        
        for result in results:
            paper = result['paper']
            videos = result['videos']
            print(f"\n论文ID: {paper['id']}")
            print(f"标题: {paper['title']}")
            print(f"作者: {', '.join(paper['authors'])}")
            if 'submitted_date' in paper:
                print(f"提交日期: {paper['submitted_date']}")
            print(f"视频数量: {len(videos)}")
            
            for j, video in enumerate(videos):
                print(f"  视频 {j+1}: {os.path.basename(video['local_path'])}")
        
        if results:
            print(f"\n所有视频已下载到: {crawler.download_folder}")
        else:
            print("\n未找到可下载的视频，可能的原因：")
            print("1. 该日期没有CS.CV论文")
            print("2. 论文没有项目主页链接")
            print("3. 项目主页没有视频内容")
            print("4. 网络连接问题")
    
    except KeyboardInterrupt:
        print("\n用户中断爬取")
    except Exception as e:
        logger.error(f"爬取过程中出错: {e}")
    finally:
        crawler.close()

if __name__ == "__main__":
    main()
