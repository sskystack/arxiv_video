#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArXiv 视频爬虫主要逻辑模块
整合论文获取、链接提取、视频下载的完整流程
"""

import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from tqdm import tqdm

# 添加 reduct_db 到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'reduct_db', 'reduct_db'))

try:
    from reduct_db.db_config.safe_session import session_factory
    from reduct_db.db_dao.paper_dao import PaperDAO
    DB_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入 reduct_db，将使用 submitted_date: {e}")
    DB_AVAILABLE = False

from utils.logger import get_logger
from core.arxiv_fetcher import get_latest_day_papers
from core.link_extractor import create_session, extract_project_links
from core.video_extractor import extract_video_urls, filter_youtube_videos_by_duration
from core.video_downloader import download_video
from core.card_generator import card_generator, generate_video_script_card
from core.video_composer import VideoComposer

logger = get_logger('arxiv_crawler')


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


class ArxivVideoCrawler:
    """ArXiv 视频爬虫"""
    
    def __init__(self, download_folder: str, max_workers: int = 4, skip_existing: bool = False, cookies_from_browser: Optional[str] = None):
        """
        初始化爬虫
        
        Args:
            download_folder: 下载目录
            max_workers: 最大线程数
            skip_existing: 是否跳过已存在res视频的论文
            cookies_from_browser: 浏览器的cookie来源，用于绕过反爬虫机制
        """
        self.download_folder = download_folder
        self.max_workers = max_workers
        self.skip_existing = skip_existing
        self.cookies_from_browser = cookies_from_browser
        self.session_pool = []
        self.results = []
        self.results_lock = threading.Lock()
        self.success_counter = ThreadSafeCounter()
        self.error_counter = ThreadSafeCounter()
        self.video_composer = VideoComposer()  # 添加视频合成器
        
        self._setup()
    
    def _setup(self):
        """初始化设置"""
        # 创建下载目录
        os.makedirs(self.download_folder, exist_ok=True)
        
        # 初始化 session 池
        for i in range(self.max_workers):
            session = create_session(cookies_from_browser=self.cookies_from_browser)
            self.session_pool.append(session)
        
        logger.info(f"初始化完成，线程数: {self.max_workers}，下载目录: {self.download_folder}")
    
    def crawl_latest_day_videos(self, field: str = 'cs.CV', max_papers: int = 1000, target_date: Optional[str] = None) -> List[Dict]:
        """
        爬取指定日期或最新一天的论文视频
        
        Args:
            field: 论文领域
            max_papers: 最大论文数量
            target_date: 指定的目标日期 (YYYYMMDD格式)，如果为None则自动获取最新日期
        
        Returns:
            成功下载的结果列表
        """
        if target_date:
            logger.info(f"开始爬取 {field} 领域 {target_date} 日期的论文视频...")
        else:
            logger.info(f"开始爬取 {field} 领域最新一天的论文视频...")
        
        # 1. 获取论文列表
        papers = get_latest_day_papers(field, max_papers, target_date)
        if not papers:
            if target_date:
                logger.error(f"未获取到 {target_date} 日期的论文列表")
            else:
                logger.error("未获取到论文列表")
            return []
        
        if target_date:
            logger.info(f"获取到 {len(papers)} 篇 {target_date} 日期的论文，开始多线程处理...")
        else:
            logger.info(f"获取到 {len(papers)} 篇论文，开始多线程处理...")
        
        # 2. 重置计数器和结果
        self.results = []
        self.success_counter = ThreadSafeCounter()
        self.error_counter = ThreadSafeCounter()
        
        # 3. 多线程处理论文
        return self._process_papers_parallel(papers)
    
    def _process_papers_parallel(self, papers: List[Dict]) -> List[Dict]:
        """并行处理论文列表"""
        total_papers = len(papers)
        
        # 创建整体进度条
        with tqdm(total=total_papers, desc="处理论文", unit="篇") as progress_bar:
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_paper = {
                    executor.submit(self._process_single_paper, paper): paper
                    for paper in papers
                }
                
                # 处理完成的任务
                for future in as_completed(future_to_paper):
                    try:
                        result = future.result()
                        if result:
                            with self.results_lock:
                                self.results.append(result)
                            self.success_counter.increment()
                        else:
                            self.error_counter.increment()
                    except Exception as e:
                        paper = future_to_paper[future]
                        logger.error(f"处理论文 {paper['id']} 时发生异常: {e}")
                        self.error_counter.increment()
                    
                    # 更新进度条
                    progress_bar.set_description(
                        f"处理论文 (成功: {self.success_counter.value}, "
                        f"失败: {self.error_counter.value})"
                    )
                    progress_bar.update(1)
        
        # 输出最终统计
        success_rate = (self.success_counter.value / total_papers * 100) if total_papers > 0 else 0
        logger.info(f"处理完成！成功: {self.success_counter.value}, "
                   f"失败: {self.error_counter.value}, "
                   f"成功率: {success_rate:.1f}%")
        
        return self.results
    
    def _process_single_paper(self, paper: Dict) -> Optional[Dict]:
        """
        处理单篇论文
        
        Args:
            paper: 论文信息字典
        
        Returns:
            成功返回包含论文和视频信息的字典，失败返回 None
        """
        paper_id = paper['id']
        title = paper['title']
        abstract_url = paper['abstract_url']
        
        # 优先使用数据库中的 publication_date，如果没有则使用 submitted_date
        publication_date = self._get_publication_date_for_paper(paper_id)
        target_date = publication_date or paper.get('submitted_date')
        date_source = "publication_date" if publication_date else "submitted_date"
        
        thread_id = threading.current_thread().ident
        logger.info(f"[线程{thread_id}] 开始处理: {paper_id} - {title[:50]}... (使用{date_source}: {target_date})")
        
        # 检查是否需要跳过已存在的论文
        if self.skip_existing:
            arxiv_id = self._extract_arxiv_id(paper_id)
            if arxiv_id and self._check_existing_res_video(arxiv_id, target_date):
                logger.info(f"[线程{thread_id}] 论文 {paper_id} 的res视频已存在，跳过处理")
                return None
        
        try:
            # 获取一个 session
            session = self._get_session()
            
            # 1. 提取项目链接
            project_links = extract_project_links(abstract_url, session)
            if not project_links:
                logger.info(f"[线程{thread_id}] 论文 {paper_id} 没有找到项目链接")
                return None
            
            # 2. 从项目页面提取并下载视频
            final_video = None
            project_urls_info = []
            
            for project_url in project_links:
                logger.info(f"[线程{thread_id}] 检查项目页面: {project_url}")
                
                # 提取视频链接（分类为YouTube和其他）
                video_data = extract_video_urls(project_url, session)
                youtube_urls = video_data.get('youtube', [])
                other_video_urls = video_data.get('other', [])
                
                project_info = {
                    'project_url': project_url,
                    'youtube_urls': youtube_urls,
                    'other_video_urls': other_video_urls
                }
                project_urls_info.append(project_info)
                
                logger.debug(f"[线程{thread_id}] 项目页面 {project_url}: YouTube视频 {len(youtube_urls)} 个，其他视频 {len(other_video_urls)} 个")
            
            # 3. 按优先级选择和下载视频
            # 优先级1: 符合时长要求的YouTube视频（1-4分钟）
            for project_info in project_urls_info:
                if project_info['youtube_urls']:
                    try:
                        # 过滤符合时长要求的YouTube视频
                        suitable_youtube = filter_youtube_videos_by_duration(
                            project_info['youtube_urls'], 
                            min_duration=60,  # 1分钟
                            max_duration=240  # 4分钟
                        )
                        
                        if suitable_youtube:
                            # 下载第一个符合要求的YouTube视频
                            youtube_url = suitable_youtube[0]
                            logger.info(f"[线程{thread_id}] 使用符合要求的YouTube视频: {youtube_url}")
                            
                            downloaded_path = download_video(
                                youtube_url, paper_id, 0, session, 
                                self.download_folder, target_date, is_primary_video=True
                            )
                            
                            if downloaded_path:
                                final_video = {
                                    'video_url': youtube_url,
                                    'local_path': downloaded_path,
                                    'project_url': project_info['project_url'],
                                    'video_type': 'youtube_primary'
                                }
                                logger.info(f"[线程{thread_id}] 成功下载YouTube主视频: {downloaded_path}")
                                break
                        else:
                            # 如果时长过滤失败，尝试下载第一个YouTube视频作为备用
                            logger.warning(f"[线程{thread_id}] 没有找到符合时长的YouTube视频，尝试第一个YouTube视频作为备用")
                            youtube_url = project_info['youtube_urls'][0]
                            logger.info(f"[线程{thread_id}] 尝试备用YouTube视频: {youtube_url}")
                            
                            downloaded_path = download_video(
                                youtube_url, paper_id, 0, session, 
                                self.download_folder, target_date, is_primary_video=True
                            )
                            
                            if downloaded_path:
                                final_video = {
                                    'video_url': youtube_url,
                                    'local_path': downloaded_path,
                                    'project_url': project_info['project_url'],
                                    'video_type': 'youtube_backup'
                                }
                                logger.info(f"[线程{thread_id}] 成功下载备用YouTube视频: {downloaded_path}")
                                break
                    except Exception as e:
                        logger.warning(f"[线程{thread_id}] 处理YouTube视频时出错: {str(e)}，继续尝试其他视频")
            
            # 优先级2: 如果没有找到合适的YouTube视频，使用第一个其他视频
            if not final_video:
                for project_info in project_urls_info:
                    if project_info['other_video_urls']:
                        other_video_url = project_info['other_video_urls'][0]
                        logger.info(f"[线程{thread_id}] 使用第一个其他视频: {other_video_url}")
                        
                        downloaded_path = download_video(
                            other_video_url, paper_id, 0, session, 
                            self.download_folder, target_date, is_primary_video=True
                        )
                        
                        if downloaded_path:
                            final_video = {
                                'video_url': other_video_url,
                                'local_path': downloaded_path,
                                'project_url': project_info['project_url'],
                                'video_type': 'other_primary'
                            }
                            logger.info(f"[线程{thread_id}] 成功下载其他主视频: {downloaded_path}")
                            break
            
            if final_video:
                logger.info(f"[线程{thread_id}] 论文 {paper_id} 成功选择并下载主视频，类型: {final_video['video_type']}")
                
                # 4. 生成视频解说卡片
                arxiv_id = self._extract_arxiv_id(paper_id)
                card = None
                composed_video_path = None
                
                if arxiv_id:
                    try:
                        # 计算卡片保存目录（与视频相同的目录）
                        video_dir = os.path.dirname(final_video['local_path'])
                        card = generate_video_script_card(arxiv_id, target_dir=video_dir)
                        if card:
                            logger.info(f"[线程{thread_id}] 成功生成并保存论文 {arxiv_id} 的解说卡片到 {video_dir}")
                            
                            # 5. 合成最终视频
                            try:
                                composed_video_path = self.video_composer.compose_paper_video(video_dir, arxiv_id)
                                if composed_video_path:
                                    logger.info(f"[线程{thread_id}] 成功为论文 {arxiv_id} 生成合成视频: {composed_video_path}")
                                else:
                                    logger.warning(f"[线程{thread_id}] 论文 {arxiv_id} 视频合成失败")
                            except Exception as e:
                                logger.error(f"[线程{thread_id}] 合成论文 {arxiv_id} 视频时出错: {e}")
                        else:
                            logger.warning(f"[线程{thread_id}] 无法为论文 {arxiv_id} 生成解说卡片")
                    except Exception as e:
                        logger.error(f"[线程{thread_id}] 生成论文 {arxiv_id} 解说卡片时出错: {e}")
                
                return {
                    'paper': paper,
                    'video': final_video,
                    'arxiv_id': arxiv_id,
                    'has_script_card': card is not None if arxiv_id else False,
                    'composed_video_path': composed_video_path
                }
            else:
                logger.info(f"[线程{thread_id}] 论文 {paper_id} 没有找到可下载的视频")
                return None
                
        except Exception as e:
            logger.error(f"[线程{thread_id}] 处理论文 {paper_id} 时出错: {e}")
            return None
    
    def _get_session(self):
        """获取一个 session（简单轮询）"""
        thread_id = threading.current_thread().ident
        session_index = abs(hash(thread_id)) % len(self.session_pool)
        return self.session_pool[session_index]
    
    def _extract_arxiv_id(self, paper_id: str) -> Optional[str]:
        """
        从论文ID中提取ArXiv ID
        
        Args:
            paper_id: 论文ID，可能是完整URL格式 "http://arxiv.org/abs/2024.12345v1" 
                     或简短格式 "2024.12345v1"，或者清理过的格式 "2024.12345"
        
        Returns:
            str: ArXiv ID（包含版本号），如 "2024.12345v1"
        """
        try:
            if 'arxiv.org/abs/' in paper_id:
                # 处理完整URL格式
                arxiv_id = paper_id.split('arxiv.org/abs/')[-1]
                return arxiv_id
            elif paper_id and '.' in paper_id:
                # 处理简短格式或清理过的格式
                if 'v' in paper_id:
                    # 已经包含版本号，直接返回
                    return paper_id
                else:
                    # 清理过的格式，需要添加v1版本号
                    return f"{paper_id}v1"
            else:
                logger.warning(f"无法识别的论文ID格式: {paper_id}")
                return None
        except Exception as e:
            logger.error(f"提取ArXiv ID失败: {e}")
            return None
    
    def _get_publication_date_for_paper(self, paper_id: str) -> Optional[str]:
        """
        从数据库中获取论文的publication_date，转换为YYYYMMDD格式
        
        Args:
            paper_id: ArXiv论文ID（如 "2508.10774" - 已经清理过的ID）
        
        Returns:
            str: 格式化的publication_date (YYYYMMDD)，如果未找到则返回None
        """
        if not DB_AVAILABLE:
            return None
        
        try:
            session = session_factory()
            paper_dao = PaperDAO(session)
            
            try:
                # 由于 arxiv_fetcher 现在返回的已经是清理过的ID (如 2508.10774)
                # 我们需要查找 external_id 为 2508.10774v1 格式的记录
                possible_external_ids = [
                    f"{paper_id}v1",  # 最常见的格式
                    f"{paper_id}v2",  # 可能的版本2
                    f"{paper_id}v3",  # 可能的版本3
                    paper_id,  # 原始格式
                ]
                
                paper = None
                for external_id in possible_external_ids:
                    papers = paper_dao.get_by_external_ids([external_id])
                    if papers:
                        paper = papers[0]
                        logger.debug(f"找到论文: {paper_id} -> external_id: {external_id}")
                        break
                
                if paper and paper.publication_date:
                    # 转换datetime为YYYYMMDD格式
                    pub_date = paper.publication_date.strftime("%Y%m%d")
                    logger.debug(f"论文 {paper_id} 的publication_date: {pub_date}")
                    return pub_date
                else:
                    logger.debug(f"论文 {paper_id} 在数据库中未找到或无publication_date")
                    return None
                    
            finally:
                session.close()
                
        except Exception as e:
            logger.debug(f"获取论文 {paper_id} 的publication_date失败: {e}")
            return None
    
    def _check_existing_res_video(self, arxiv_id: str, target_date: str) -> bool:
        """
        检查指定论文的res视频是否已存在
        
        Args:
            arxiv_id: ArXiv ID（如 "2508.10774"）
            target_date: 目标日期（如 "20250821"）
        
        Returns:
            bool: 如果res视频已存在返回True，否则返回False
        """
        try:
            # 构建可能的视频文件路径
            paper_folder = os.path.join(self.download_folder, target_date, arxiv_id)
            res_video_path = os.path.join(paper_folder, f"{arxiv_id}_res.mp4")
            
            if os.path.exists(res_video_path):
                # 检查文件大小，确保不是空文件
                file_size = os.path.getsize(res_video_path)
                if file_size > 1024:  # 大于1KB，认为是有效文件
                    logger.debug(f"发现已存在的res视频: {res_video_path} (大小: {file_size/1024/1024:.1f}MB)")
                    return True
                else:
                    logger.debug(f"res视频文件太小，可能损坏: {res_video_path} (大小: {file_size}字节)")
                    return False
            
            return False
            
        except Exception as e:
            logger.warning(f"检查res视频是否存在时出错: {e}")
            return False
    
    def close(self):
        """清理资源"""
        for session in self.session_pool:
            session.close()
        logger.info("爬虫资源已清理")
