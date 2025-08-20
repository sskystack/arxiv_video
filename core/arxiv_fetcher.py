#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArXiv 论文信息获取模块
负责从数据库获取最新发布日期的论文信息
"""

import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import arxiv
from utils.logger import get_logger
from reduct_db.db_config.safe_session import session_factory
from reduct_db.db_dao.paper_dao import PaperDAO
from sqlalchemy import func, desc

logger = get_logger('arxiv_fetcher')


def get_latest_day_papers(field: str = 'cs.CV', max_papers: int = 1000, target_date: Optional[str] = None) -> List[Dict]:
    """
    从数据库获取指定或最新发布日期的所有论文，失败时自动回退到API方法
    
    Args:
        field: 论文领域，默认 'cs.CV' (在数据库版本中暂时不起作用，API回退时使用)
        max_papers: 最大论文数量
        target_date: 指定的目标日期 (YYYYMMDD格式)，如果为None则自动获取最新日期
    
    Returns:
        论文信息列表，每个字典包含 id, title, abstract_url, authors, submitted_date
    """
    if target_date:
        logger.info(f"开始从数据库获取指定日期 {target_date} 的论文...")
    else:
        logger.info(f"开始从数据库获取最新发布日的论文...")
    
    try:
        # 如果指定了日期，直接使用；否则获取最新日期
        if target_date:
            latest_date = target_date
            logger.info(f"使用指定的发布日期: {latest_date}")
        else:
            # 优先尝试从数据库获取最新日期
            latest_date = _get_latest_publication_date_from_db()
            if not latest_date:
                logger.warning("无法从数据库确定最新发布日期，回退到API方法")
                return get_latest_day_papers_from_api(field, max_papers)
            logger.info(f"数据库中最新发布日期: {latest_date}")
        
        # 获取该日期的所有论文
        papers = _get_papers_by_publication_date(latest_date, max_papers)
        
        if not papers:
            if target_date:
                logger.warning(f"数据库中没有找到 {target_date} 日期的论文")
                return []
            else:
                logger.warning("数据库中没有找到论文，回退到API方法")
                return get_latest_day_papers_from_api(field, max_papers)
        
        return papers
        
    except Exception as e:
        if target_date:
            logger.error(f"从数据库获取指定日期 {target_date} 论文失败: {e}")
            return []
        else:
            logger.error(f"从数据库获取论文失败: {e}，回退到API方法")
            return get_latest_day_papers_from_api(field, max_papers)


def _get_latest_publication_date_from_db() -> Optional[str]:
    """从数据库获取最新的论文发布日期"""
    try:
        session = session_factory()
        paper_dao = PaperDAO(session)
        
        # 查询最新的publication_date，按publication_date降序排列
        latest_paper = session.query(paper_dao.model_cls).filter(
            paper_dao.model_cls.is_deleted == 0,
            paper_dao.model_cls.publication_date.isnot(None)
        ).order_by(desc(paper_dao.model_cls.publication_date)).first()
        
        if latest_paper and latest_paper.publication_date:
            # 将publication_date转换为YYYYMMDD格式
            if hasattr(latest_paper.publication_date, 'strftime'):
                return latest_paper.publication_date.strftime("%Y%m%d")
            else:
                # 如果是字符串格式，需要解析后转换
                return latest_paper.publication_date
        
        return None
        
    except Exception as e:
        logger.error(f"从数据库获取最新日期失败: {e}")
        return None
    finally:
        if 'session' in locals():
            session.close()


def _get_papers_by_publication_date(target_date: str, max_papers: int) -> List[Dict]:
    """
    从数据库获取指定发布日期的论文列表
    
    Args:
        target_date: 目标日期 (YYYYMMDD 格式)
        max_papers: 最大论文数量
    
    Returns:
        论文信息列表
    """
    logger.info(f"正在从数据库获取 {target_date} 日期的论文...")
    
    try:
        session = session_factory()
        paper_dao = PaperDAO(session)
        
        # 将YYYYMMDD格式转换为date对象用于查询
        target_date_obj = datetime.strptime(target_date, "%Y%m%d").date()
        
        # 查询指定日期的所有论文
        papers_from_db = session.query(paper_dao.model_cls).filter(
            paper_dao.model_cls.is_deleted == 0,
            func.date(paper_dao.model_cls.publication_date) == target_date_obj
        ).limit(max_papers).all()
        
        papers = []
        for paper in papers_from_db:
            # 处理external_id，去掉最后两个字符（例如从2508.13229v1变为2508.13229）
            external_id = paper.external_id
            if external_id and len(external_id) > 2:
                # 去掉最后两个字符(如v1)
                clean_id = external_id[:-2]
            else:
                clean_id = external_id
            
            paper_info = {
                'id': clean_id,
                'title': paper.title or 'Unknown Title',
                'abstract_url': f"https://arxiv.org/abs/{clean_id}",
                'authors': _extract_authors(paper),  # 需要从数据库中提取作者信息
                'submitted_date': target_date,  # 使用publication_date作为submitted_date
                'published_date': paper.publication_date.strftime("%Y-%m-%d %H:%M:%S") if paper.publication_date else target_date,
                'external_id': external_id,  # 保留原始external_id用于调试
                'database_id': paper.id  # 保留数据库ID用于后续处理
            }
            papers.append(paper_info)
        
        logger.info(f"从数据库获取完成，共找到 {len(papers)} 篇 {target_date} 日期的论文")
        
        if len(papers) == 0:
            logger.warning(f"数据库中未找到 {target_date} 日期的论文")
        
        return papers
        
    except Exception as e:
        logger.error(f"从数据库获取 {target_date} 日期论文失败: {e}")
        return []
    finally:
        if 'session' in locals():
            session.close()


def _extract_authors(paper) -> List[str]:
    """从论文对象中提取作者信息"""
    try:
        # 这里需要根据您的数据库结构来提取作者信息
        # 假设有authors字段或者关联的authors表
        if hasattr(paper, 'authors') and paper.authors:
            return [paper.authors]  # 如果authors是字符串
        elif hasattr(paper, 'author') and paper.author:
            return [paper.author]
        else:
            return ['Unknown Author']
    except Exception as e:
        logger.warning(f"提取作者信息失败: {e}")
        return ['Unknown Author']


# ====== API备用方法 (从备份文件保留) ======
def get_latest_day_papers_from_api(field: str = 'cs.CV', max_papers: int = 1000) -> List[Dict]:
    """
    API备用方法：从ArXiv API获取最新发布日的论文
    当数据库方法失败时使用此方法
    """
    logger.info(f"使用API备用方法获取 {field} 领域最新发布日的论文...")
    
    try:
        # 先获取最新论文确定日期
        latest_date = _get_latest_submission_date_from_api(field)
        if not latest_date:
            logger.error("无法确定最新发布日期")
            return []
        
        logger.info(f"API最新发布日期: {latest_date}")
        
        # 获取该日期的所有论文
        return _get_papers_by_date_from_api(field, latest_date, max_papers)
        
    except Exception as e:
        logger.error(f"API获取最新日期论文失败: {e}")
        return []


def _get_latest_submission_date_from_api(field: str) -> Optional[str]:
    """API备用方法：获取最新的论文发布日期"""
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=f"cat:{field}",
            max_results=1,
            sort_by=arxiv.SortCriterion.LastUpdatedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        for result in client.results(search):
            return result.published.strftime("%Y%m%d")
        
        return None
        
    except Exception as e:
        logger.error(f"API获取最新日期失败: {e}")
        return None


def _get_papers_by_date_from_api(field: str, target_date: str, max_papers: int) -> List[Dict]:
    """
    API备用方法：获取指定日期的论文列表
    """
    logger.info(f"正在通过API获取 {target_date} 日期的 {field} 论文...")
    
    try:
        client = arxiv.Client()
        papers = []
        processed_ids = set()
        
        # 计算搜索范围
        target_date_obj = datetime.strptime(target_date, "%Y%m%d")
        prev_date = (target_date_obj - timedelta(days=1)).strftime("%Y%m%d")
        
        # 创建搜索请求，搜索更多论文以确保完整性
        search_size = max(max_papers * 10, 2000)
        search = arxiv.Search(
            query=f"cat:{field}",
            max_results=search_size,
            sort_by=arxiv.SortCriterion.LastUpdatedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        paper_count = 0
        target_date_papers = 0
        seen_dates = set()
        
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
                
                if len(papers) >= max_papers:
                    logger.info(f"已找到足够多的目标日期论文: {len(papers)} 篇")
                    break
            
            # 每处理100篇论文输出一次进度
            if paper_count % 100 == 0:
                logger.info(f"已处理 {paper_count} 篇论文，目标日期论文: {target_date_papers} 篇")
            
            # 完整性检查：如果已经看到前一天的论文，说明搜索足够深入
            if prev_date in seen_dates and target_date_papers > 0:
                logger.info("完整性检查通过，已搜索到前一天的论文")
                break
            
            # 避免搜索过深
            if paper_count >= search_size:
                break
        
        logger.info(f"API搜索完成，共找到 {len(papers)} 篇 {target_date} 日期的论文")
        
        return papers
        
    except Exception as e:
        logger.error(f"API获取 {target_date} 日期论文失败: {e}")
        return []
