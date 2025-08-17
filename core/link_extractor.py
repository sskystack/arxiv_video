#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目链接提取模块
从 ArXiv 摘要页面提取项目主页链接
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from typing import List, Set
from urllib.parse import urljoin, urlparse
from utils.logger import get_logger

logger = get_logger('link_extractor')


# 用户代理列表
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.123 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:88.0) Gecko/20100101 Firefox/88.0',
]

# 黑名单链接（需要过滤的链接）
BLACKLIST_URLS = [
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


def create_session() -> requests.Session:
    """创建配置好的 requests session"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': random.choice(USER_AGENTS)
    })
    return session


def extract_project_links(abstract_url: str, session: requests.Session) -> List[str]:
    """
    从 ArXiv 摘要页面提取项目链接
    
    Args:
        abstract_url: ArXiv 摘要页面 URL
        session: requests session
    
    Returns:
        项目链接列表
    """
    logger.debug(f"提取项目链接: {abstract_url}")
    
    try:
        # 随机延迟，避免过于频繁的请求
        time.sleep(random.uniform(0.2, 1.0))
        
        response = session.get(abstract_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        project_links = _find_project_links(soup)
        
        return list(set(project_links))  # 去重
        
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            logger.warning(f"摘要页面无法访问 (404): {abstract_url}")
        else:
            logger.error(f"HTTP错误: {http_err}")
        return []
    except Exception as e:
        logger.error(f"提取项目链接失败: {e}")
        return []


def _find_project_links(soup: BeautifulSoup) -> List[str]:
    """在页面中查找项目链接"""
    project_links = []
    
    # 查找所有外部链接
    external_links = soup.find_all('a', href=True)
    
    for link in external_links:
        href = link.get('href', '')
        text = link.get_text(strip=True).lower()
        
        # 检查是否在黑名单中
        if _is_blacklisted(href):
            continue
        
        # 判断是否为项目页面链接
        if _is_project_link(href, text):
            if href.startswith('http'):
                project_links.append(href)
                logger.debug(f"找到项目链接: {href}")
    
    return project_links


def _is_blacklisted(href: str) -> bool:
    """检查链接是否在黑名单中"""
    return any(blacklist in href for blacklist in BLACKLIST_URLS)


def _is_project_link(href: str, text: str) -> bool:
    """判断是否为项目链接"""
    # 检查 URL 中的关键词
    url_keywords = ['github.io', 'project', 'demo', 'page']
    if any(keyword in href for keyword in url_keywords):
        return True
    
    # 检查链接文本中的关键词
    text_keywords = ['project', 'demo', 'page', 'website']
    if any(keyword in text for keyword in text_keywords):
        return True
    
    return False
