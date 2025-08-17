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
from core.video_extractor import extract_video_urls
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
    
    def __init__(self, download_folder: str, max_workers: int = 4):
        """
        初始化爬虫
        
        Args:
            download_folder: 下载目录
            max_workers: 最大线程数
        """
        self.download_folder = download_folder
        self.max_workers = max_workers
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
            session = create_session()
            self.session_pool.append(session)
        
        logger.info(f"初始化完成，线程数: {self.max_workers}，下载目录: {self.download_folder}")
    
    def crawl_latest_day_videos(self, field: str = 'cs.CV', max_papers: int = 1000) -> List[Dict]:
        """
        爬取最新一天的论文视频
        
        Args:
            field: 论文领域
            max_papers: 最大论文数量
        
        Returns:
            成功下载的结果列表
        """
        logger.info(f"开始爬取 {field} 领域最新一天的论文视频...")
        
        # 1. 获取论文列表
        papers = get_latest_day_papers(field, max_papers)
        if not papers:
            logger.error("未获取到论文列表")
            return []
        
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
        
        try:
            # 获取一个 session
            session = self._get_session()
            
            # 1. 提取项目链接
            project_links = extract_project_links(abstract_url, session)
            if not project_links:
                logger.info(f"[线程{thread_id}] 论文 {paper_id} 没有找到项目链接")
                return None
            
            # 2. 从项目页面提取并下载视频
            paper_videos = []
            for project_url in project_links:
                logger.info(f"[线程{thread_id}] 检查项目页面: {project_url}")
                
                # 提取视频链接
                video_urls = extract_video_urls(project_url, session)
                if not video_urls:
                    logger.debug(f"[线程{thread_id}] 项目页面 {project_url} 没有找到视频")
                    continue
                
                # 下载视频
                for j, video_url in enumerate(video_urls):
                    downloaded_path = download_video(
                        video_url, paper_id, j, session, 
                        self.download_folder, target_date
                    )
                    if downloaded_path:
                        paper_videos.append({
                            'video_url': video_url,
                            'local_path': downloaded_path,
                            'project_url': project_url
                        })
            
            if paper_videos:
                logger.info(f"[线程{thread_id}] 论文 {paper_id} 成功下载 {len(paper_videos)} 个视频")
                
                # 3. 生成视频解说卡片
                arxiv_id = self._extract_arxiv_id(paper_id)
                card = None
                composed_video_path = None
                
                if arxiv_id:
                    try:
                        # 计算卡片保存目录（与视频相同的目录）
                        video_dir = os.path.dirname(paper_videos[0]['local_path'])
                        card = generate_video_script_card(arxiv_id, target_dir=video_dir)
                        if card:
                            logger.info(f"[线程{thread_id}] 成功生成并保存论文 {arxiv_id} 的解说卡片到 {video_dir}")
                            
                            # 4. 合成最终视频
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
                    'videos': paper_videos,
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
                     或简短格式 "2024.12345v1"
        
        Returns:
            str: ArXiv ID（包含版本号），如 "2024.12345v1"
        """
        try:
            if 'arxiv.org/abs/' in paper_id:
                # 处理完整URL格式
                arxiv_id = paper_id.split('arxiv.org/abs/')[-1]
                return arxiv_id
            elif paper_id and '.' in paper_id and 'v' in paper_id:
                # 处理简短格式，直接返回
                return paper_id
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
            paper_id: ArXiv论文ID（如 "2508.10774v1"）
        
        Returns:
            str: 格式化的publication_date (YYYYMMDD)，如果未找到则返回None
        """
        if not DB_AVAILABLE:
            return None
        
        try:
            # 清理ArXiv ID，移除版本号
            clean_id = paper_id.replace('v', '.').split('.')[0] + '.' + paper_id.replace('v', '.').split('.')[1]
            
            session = session_factory()
            paper_dao = PaperDAO(session)
            
            try:
                # 尝试原始ID和清理后的ID
                paper = paper_dao.get_by_external_id(paper_id) or paper_dao.get_by_external_id(clean_id)
                
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
    
    def close(self):
        """清理资源"""
        for session in self.session_pool:
            session.close()
        logger.info("爬虫资源已清理")
