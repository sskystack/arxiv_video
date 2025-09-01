#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频下载模块
负责下载视频文件，支持 YouTube、Bilibili 等平台以及直接链接
"""

import os
import time
import random
import requests
import yt_dlp
from datetime import datetime
from typing import Optional
from tqdm import tqdm
from utils.logger import get_logger
from core.link_extractor import USER_AGENTS

logger = get_logger('video_downloader')


def download_video(
    video_url: str,
    paper_id: str,
    video_index: int,
    session: requests.Session,
    download_folder: str,
    target_date: Optional[str] = None,
    max_retries: int = 3,
    is_primary_video: bool = False
) -> Optional[str]:
    """
    下载视频文件
    
    Args:
        video_url: 视频 URL
        paper_id: 论文 ID
        video_index: 视频索引
        session: requests session
        download_folder: 下载目录
        target_date: 目标日期
        max_retries: 最大重试次数
        is_primary_video: 是否为主要视频（用于命名）
    
    Returns:
        下载成功的文件路径，失败返回 None
    """
    logger.debug(f"开始下载视频: {video_url}")
    
    # 创建下载目录
    save_path = _create_download_path(download_folder, paper_id, target_date)
    
    # 根据 URL 类型选择下载方式
    if _is_video_platform(video_url):
        # 硬编码使用chrome的cookies来绕过YouTube的bot检测
        return _download_with_ytdlp(video_url, paper_id, video_index, save_path, is_primary_video, cookies_from_browser='chrome')
    else:
        return _download_with_requests(
            video_url, paper_id, video_index, session, save_path, max_retries, is_primary_video
        )


def _create_download_path(download_folder: str, paper_id: str, target_date: Optional[str]) -> str:
    """创建下载路径"""
    if target_date:
        date_folder_name = target_date.replace('-', '') if len(target_date) == 10 else target_date
    else:
        date_folder_name = datetime.now().strftime("%Y%m%d")
    
    date_folder = os.path.join(download_folder, date_folder_name)
    
    # 清理论文 ID 中的非法字符
    safe_paper_id = _sanitize_filename(paper_id)
    paper_folder = os.path.join(date_folder, safe_paper_id)
    
    os.makedirs(paper_folder, exist_ok=True)
    return paper_folder


def _sanitize_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    import re
    # 只保留字母、数字、点号、下划线和连字符
    return re.sub(r'[^\w\.-]', '_', filename)


def _is_video_platform(video_url: str) -> bool:
    """检查是否为视频平台链接"""
    return 'youtube.com' in video_url or 'bilibili.com' in video_url


def _download_with_ytdlp(video_url: str, paper_id: str, video_index: int, save_path: str, is_primary_video: bool = False, cookies_from_browser: Optional[str] = None) -> Optional[str]:
    """使用 yt-dlp 下载视频"""
    logger.info(f"使用 yt-dlp 下载视频: {video_url}")

    try:
        # 根据是否为主要视频决定文件名
        if is_primary_video:
            filename_template = "primary_video.%(ext)s"
        else:
            filename_template = f"video_{video_index}.%(ext)s"

        # 配置 yt-dlp 选项
        ydl_opts = {
            'format': 'bestvideo[height>=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(save_path, filename_template),
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        # 如果提供了 cookies_from_browser 参数，添加到 yt-dlp 命令行参数
        ydl_command = ["yt-dlp"]
        
        # 添加格式参数
        ydl_command.extend(["-f", "bestvideo[height>=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"])
        
        # 添加输出文件名模板
        output_template = os.path.join(save_path, filename_template)
        ydl_command.extend(["-o", output_template])
        
        # 添加其他参数
        ydl_command.extend(["--no-playlist", "--merge-output-format", "mp4"])
        
        # 如果提供了cookies_from_browser参数
        if cookies_from_browser:
            ydl_command.extend(["--cookies-from-browser", cookies_from_browser])
            
        # 添加视频URL
        ydl_command.append(video_url)

        # 使用 subprocess 调用 yt-dlp
        import subprocess
        logger.info(f"执行命令: {' '.join(ydl_command)}")
        result = subprocess.run(ydl_command, capture_output=True, text=True, cwd=save_path)

        if result.returncode != 0:
            logger.error(f"yt-dlp 下载失败: {result.stderr}")
            return None

        # 查找下载的文件
        if is_primary_video:
            expected_path = os.path.join(save_path, "primary_video.mp4")
        else:
            expected_path = os.path.join(save_path, f"video_{video_index}.mp4")

        if os.path.exists(expected_path):
            logger.info(f"yt-dlp 下载成功: {expected_path}")
            return expected_path

        # 尝试其他可能的扩展名
        for ext in ['mkv', 'webm']:
            if is_primary_video:
                alt_path = os.path.join(save_path, f"primary_video.{ext}")
            else:
                alt_path = os.path.join(save_path, f"video_{video_index}.{ext}")

            if os.path.exists(alt_path):
                logger.info(f"yt-dlp 下载成功: {alt_path}")
                return alt_path

        logger.warning(f"yt-dlp 下载后未找到文件: {video_url}")
        return None

    except Exception as e:
        logger.error(f"yt-dlp 下载失败: {e}")
        return None


def _download_with_requests(
    video_url: str,
    paper_id: str,
    video_index: int,
    session: requests.Session,
    save_path: str,
    max_retries: int,
    is_primary_video: bool = False
) -> Optional[str]:
    """使用 requests 下载视频"""
    logger.debug(f"使用 requests 下载视频: {video_url}")
    
    for retry in range(max_retries):
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'video/mp4,video/*;q=0.9,*/*;q=0.8',
                'Referer': _get_safe_referer(video_url),
            }
            
            response = session.get(video_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # 检查文件大小
            file_size = int(response.headers.get('content-length', 0))
            if file_size > 500 * 1024 * 1024:  # 500MB 限制
                logger.warning(f"视频文件过大 ({file_size/1024/1024:.1f}MB)，跳过下载")
                return None
            
            # 确定文件扩展名
            ext = _get_file_extension(response, video_url)
            
            # 根据是否为主要视频决定文件名
            if is_primary_video:
                filename = f"primary_video{ext}"
            else:
                filename = f"video_{video_index}{ext}"
                
            filepath = os.path.join(save_path, filename)
            
            # 下载文件
            _download_file_with_progress(response, filepath, filename)
            
            logger.info(f"视频下载成功: {filepath}")
            return filepath
            
        except Exception as e:
            if retry < max_retries - 1:
                logger.warning(f"下载失败，重试 {retry+1}/{max_retries}: {e}")
                time.sleep(random.uniform(2, 5))
            else:
                logger.error(f"视频下载最终失败: {e}")
    
    return None


def _get_safe_referer(video_url: str) -> str:
    """安全地构建 Referer 头"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(video_url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return video_url


def _get_file_extension(response: requests.Response, video_url: str) -> str:
    """确定文件扩展名"""
    content_type = response.headers.get('content-type', '').lower()
    
    if 'mp4' in content_type:
        return '.mp4'
    elif 'webm' in content_type:
        return '.webm'
    elif video_url.lower().endswith('.mp4'):
        return '.mp4'
    elif video_url.lower().endswith('.webm'):
        return '.webm'
    else:
        return '.mp4'  # 默认


def _download_file_with_progress(response: requests.Response, filepath: str, filename: str) -> None:
    """带进度条的文件下载"""
    file_size = int(response.headers.get('content-length', 0))
    
    with open(filepath, 'wb') as f:
        if file_size > 0:
            # 有文件大小信息，显示进度条
            with tqdm(
                total=file_size,
                unit='B',
                unit_scale=True,
                desc=f"下载 {filename}",
                leave=False
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        else:
            # 无文件大小信息，简单下载
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
