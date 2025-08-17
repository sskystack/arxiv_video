#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频提取模块
从项目页面提取视频链接
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import urljoin, urlparse, parse_qs
from utils.logger import get_logger
from core.link_extractor import USER_AGENTS

logger = get_logger('video_extractor')


def extract_video_urls(project_url: str, session: requests.Session) -> List[str]:
    """
    从项目页面提取视频 URL
    
    Args:
        project_url: 项目页面 URL
        session: requests session
    
    Returns:
        视频 URL 列表
    """
    logger.debug(f"提取视频URL: {project_url}")
    
    try:
        # 随机延迟
        time.sleep(random.uniform(0.5, 1.5))
        
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
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 确定基准 URL
        base_url = _get_base_url(soup, project_url)
        
        video_urls = []
        
        # 查找各种类型的视频链接
        video_urls.extend(_find_video_tags(soup, base_url))
        video_urls.extend(_find_iframe_videos(soup, base_url))
        video_urls.extend(_find_direct_video_links(soup, base_url))
        
        return list(set(video_urls))  # 去重
        
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            logger.warning(f"项目页面无法访问 (404): {project_url}")
        else:
            logger.error(f"访问项目页面HTTP错误: {http_err}")
        return []
    except Exception as e:
        logger.error(f"提取视频URL失败: {e}")
        return []


def _get_base_url(soup: BeautifulSoup, project_url: str) -> str:
    """获取页面的基准 URL"""
    base_tag = soup.find('base', href=True)
    base_url = base_tag['href'] if base_tag else project_url
    
    # 确保基准URL以 / 结尾
    if not base_url.endswith('/'):
        base_url += '/'
    
    logger.debug(f"使用基准URL: {base_url}")
    return base_url


def _find_video_tags(soup: BeautifulSoup, base_url: str) -> List[str]:
    """查找 video 标签中的视频"""
    video_urls = []
    
    videos = soup.find_all('video')
    for video in videos:
        # 优先使用 video 标签的 src 属性
        src = video.get('src')
        if src:
            full_url = urljoin(base_url, src)
            video_urls.append(full_url)
            logger.debug(f"找到 <video> 标签视频: {full_url}")
        
        # 查找内部的 source 标签
        sources = video.find_all('source')
        for source in sources:
            src = source.get('src')
            if src:
                full_url = urljoin(base_url, src)
                video_urls.append(full_url)
                logger.debug(f"找到 <source> 标签视频: {full_url}")
    
    return video_urls


def _find_iframe_videos(soup: BeautifulSoup, base_url: str) -> List[str]:
    """查找 iframe 中的视频（YouTube、Bilibili等）"""
    video_urls = []
    
    iframes = soup.find_all('iframe')
    for iframe in iframes:
        src = iframe.get('src')
        if not src:
            continue
        
        # YouTube 嵌入链接
        if 'youtube.com/embed/' in src:
            full_url = urljoin(base_url, src)
            video_urls.append(full_url)
            logger.debug(f"找到YouTube嵌入视频: {full_url}")
        
        # Bilibili 嵌入链接
        elif 'player.bilibili.com' in src:
            converted_url = _convert_bilibili_url(src)
            video_urls.append(converted_url)
            logger.debug(f"找到并转换Bilibili链接: {src} -> {converted_url}")
    
    return video_urls


def _find_direct_video_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """查找直接指向视频文件的链接"""
    video_urls = []
    
    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link.get('href')
        if href and href.lower().endswith(('.mp4', '.webm', '.avi', '.mov')):
            full_url = urljoin(base_url, href)
            video_urls.append(full_url)
            logger.debug(f"找到直接视频链接: {full_url}")
    
    return video_urls


def _convert_bilibili_url(url: str) -> str:
    """将 Bilibili 嵌入式 URL 转换为标准视频 URL"""
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        bvid = query_params.get('bvid', [None])[0]
        if bvid:
            return f"https://www.bilibili.com/video/{bvid}"
            
        aid = query_params.get('aid', [None])[0]
        if aid:
            return f"https://www.bilibili.com/video/av{aid}"
    except Exception:
        pass
    
    # 如果无法转换，返回原URL
    return url
