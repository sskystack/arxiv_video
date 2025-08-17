#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志配置模块
按日期分类保存日志文件，支持控制台和文件双输出
"""

import os
import logging
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str = 'arxiv_crawler',
    log_level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    配置并返回日志器
    
    Args:
        name: 日志器名称
        log_level: 日志级别
        console_output: 是否输出到控制台
    
    Returns:
        配置好的日志器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.hasHandlers():
        logger.handlers.clear()
    
    logger.setLevel(log_level)
    
    # 创建日志目录
    log_dir = _get_log_directory()
    
    # 创建文件处理器 - 按日期命名
    file_handler = _create_file_handler(log_dir, log_level)
    logger.addHandler(file_handler)
    
    # 创建控制台处理器
    if console_output:
        console_handler = _create_console_handler(log_level)
        logger.addHandler(console_handler)
    
    return logger


def _get_log_directory() -> str:
    """获取日志目录路径"""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(script_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _create_file_handler(log_dir: str, log_level: int) -> logging.FileHandler:
    """创建文件处理器"""
    today = datetime.now().strftime('%Y-%m-%d')
    log_filename = f"arxiv_crawler_{today}.log"
    log_filepath = os.path.join(log_dir, log_filename)
    
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # 详细的文件日志格式
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    return file_handler


def _create_console_handler(log_level: int) -> logging.StreamHandler:
    """创建控制台处理器"""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 简洁的控制台日志格式
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    return console_handler


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志器的便捷函数
    
    Args:
        name: 日志器名称，如果为 None 则使用默认名称
    
    Returns:
        日志器实例
    """
    if name is None:
        name = 'arxiv_crawler'
    
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        return setup_logger(name)
    return logger
