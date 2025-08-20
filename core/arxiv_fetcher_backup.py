#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArXiv 论文信息获取模块 - 备份版本
负责从 ArXiv 获取指定日期的论文信息（原API方式）
"""

import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import arxiv
from utils.logger import get_logger

logger = get_logger('arxiv_fetcher')


def get_latest_day_papers(field: str = 'cs.CV', max_papers: int = 1000) -> List[Dict]:
    """
    获取指定领域最新发布日的所有论文
    
    Args:
        field: 论文领域，默认 'cs.CV'
        max_papers: 最大论文数量
    
    Returns:
        论文信息列表，每个字典包含 id, title, abstract_url, authors, submitted_date
    """
    logger.info(f"开始获取 {field} 领域最新发布日的论文...")
    
    try:
        # 先获取最新论文确定日期
        latest_date = _get_latest_submission_date(field)
        if not latest_date:
            logger.error("无法确定最新发布日期")
            return []
        
        logger.info(f"最新发布日期: {latest_date}")
        
        # 获取该日期的所有论文
        return _get_papers_by_date(field, latest_date, max_papers)
        
    except Exception as e:
        logger.error(f"获取最新日期论文失败: {e}")
        return []


def _get_latest_submission_date(field: str) -> Optional[str]:
    """获取最新的论文发布日期"""
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
        logger.error(f"获取最新日期失败: {e}")
        return None


def _get_papers_by_date(field: str, target_date: str, max_papers: int) -> List[Dict]:
    """
    获取指定日期的论文列表
    
    Args:
        field: 论文领域
        target_date: 目标日期 (YYYYMMDD 格式)
        max_papers: 最大论文数量
    
    Returns:
        论文信息列表
    """
    logger.info(f"正在获取 {target_date} 日期的 {field} 论文...")
    
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
        
        logger.info(f"搜索完成，共找到 {len(papers)} 篇 {target_date} 日期的论文")
        
        if len(papers) == 0:
            logger.warning(f"未找到 {target_date} 日期的 {field} 论文")
            if seen_dates:
                closest_dates = sorted([d for d in seen_dates if abs(
                    (datetime.strptime(d, "%Y%m%d") - target_date_obj).days) <= 3])
                if closest_dates:
                    logger.info(f"附近有论文的日期: {closest_dates}")
        
        return papers
        
    except Exception as e:
        logger.error(f"获取 {target_date} 日期论文失败: {e}")
        return []
