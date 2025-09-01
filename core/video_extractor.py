#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频提取模块
从项目页面提取视频链接
"""

import time
import random
import requests
import yt_dlp
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from utils.logger import get_logger
from core.link_extractor import USER_AGENTS

logger = get_logger('video_extractor')


def extract_video_urls(project_url: str, session: requests.Session) -> Dict[str, List[str]]:
    """
    从项目页面提取视频 URL
    
    Args:
        project_url: 项目页面 URL
        session: requests session
    
    Returns:
        包含不同类型视频的字典:
        {
            'youtube': [YouTube链接列表],
            'other': [其他视频链接列表]
        }
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
        
        youtube_urls = []
        other_video_urls = []
        
        # 查找各种类型的视频链接
        video_links = []
        video_links.extend(_find_video_tags(soup, base_url))
        video_links.extend(_find_iframe_videos(soup, base_url))
        video_links.extend(_find_direct_video_links(soup, base_url))
        video_links.extend(_find_youtube_links(soup, base_url))
        
        # 分类视频链接
        for url in set(video_links):  # 去重
            if _is_youtube_url(url):
                youtube_urls.append(url)
            else:
                other_video_urls.append(url)
        
        return {
            'youtube': youtube_urls,
            'other': other_video_urls
        }
        
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            logger.warning(f"项目页面无法访问 (404): {project_url}")
        else:
            logger.error(f"访问项目页面HTTP错误: {http_err}")
        return {'youtube': [], 'other': []}
    except Exception as e:
        logger.error(f"提取视频URL失败: {e}")
        return {'youtube': [], 'other': []}


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
            # 转换嵌入链接为普通观看链接
            youtube_url = _convert_youtube_embed_to_watch(full_url)
            video_urls.append(youtube_url)
            logger.debug(f"找到YouTube嵌入视频: {full_url} -> {youtube_url}")
        
        # Bilibili 嵌入链接
        elif 'player.bilibili.com' in src:
            converted_url = _convert_bilibili_url(src)
            video_urls.append(converted_url)
            logger.debug(f"找到并转换Bilibili链接: {src} -> {converted_url}")
    
    return video_urls


def _find_youtube_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """查找页面中的YouTube链接"""
    youtube_urls = []
    
    # 查找所有链接
    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link.get('href')
        if href and _is_youtube_url(href):
            full_url = urljoin(base_url, href)
            youtube_urls.append(full_url)
            logger.debug(f"找到YouTube链接: {full_url}")
    
    # 查找页面内容中的YouTube链接
    page_text = soup.get_text()
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://youtu\.be/[\w-]+',
    ]
    
    for pattern in youtube_patterns:
        matches = re.findall(pattern, page_text)
        for match in matches:
            youtube_urls.append(match)
            logger.debug(f"在文本中找到YouTube链接: {match}")
    
    return youtube_urls


def _is_youtube_url(url: str) -> bool:
    """判断是否为YouTube链接"""
    return ('youtube.com' in url and '/watch' in url) or 'youtu.be' in url or 'youtube.com/embed' in url


def _convert_youtube_embed_to_watch(embed_url: str) -> str:
    """将YouTube嵌入链接转换为普通观看链接"""
    try:
        # 提取视频ID
        if '/embed/' in embed_url:
            video_id = embed_url.split('/embed/')[-1].split('?')[0]
            return f"https://www.youtube.com/watch?v={video_id}"
    except Exception:
        pass
    return embed_url


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


def get_youtube_video_duration(url: str) -> float:
    """获取YouTube视频时长（秒）"""
    import subprocess
    try:
        # 添加cookies-from-browser参数以绕过YouTube的bot检测
        cmd = [
            "yt-dlp", 
            "--print", "duration",
            "--no-download",
            "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "--extractor-retries", "3",
            "--sleep-interval", "1",
            "--max-sleep-interval", "3",
            "--cookies-from-browser", "chrome",
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
            logger.info(f"YouTube视频时长: {duration}秒")
            return duration
        else:
            logger.error(f"获取YouTube视频时长失败: {result.stderr}")
            return -1
            
    except Exception as e:
        logger.error(f"获取YouTube视频时长失败: {str(e)}")
        return -1


def filter_youtube_videos_by_duration(youtube_urls: List[str], min_duration: int = 60, max_duration: int = 240) -> List[str]:
    """
    根据时长过滤YouTube视频
    
    Args:
        youtube_urls: YouTube视频URL列表
        min_duration: 最小时长（秒，默认60秒）
        max_duration: 最大时长（秒，默认240秒）
    
    Returns:
        符合时长要求的YouTube视频URL列表
    """
    filtered_urls = []
    
    for url in youtube_urls:
        duration = get_youtube_video_duration(url)
        if duration and min_duration <= duration <= max_duration:
            logger.info(f"YouTube视频 {url} 时长 {duration}秒，符合要求({min_duration}-{max_duration}秒)")
            filtered_urls.append(url)
        elif duration:
            logger.info(f"YouTube视频 {url} 时长 {duration}秒，不符合要求({min_duration}-{max_duration}秒)")
        else:
            logger.warning(f"无法获取YouTube视频 {url} 的时长信息，跳过")
    
    return filtered_urls


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
