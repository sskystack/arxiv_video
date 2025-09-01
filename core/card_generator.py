#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频解说卡片生成模块
从 reduct_db 数据库中根据 ArXiv ID 查询论文信息，生成标准化的解说卡片
"""

import sys
import os
import re
import json
from typing import Optional, List
from datetime import datetime

# 添加 reduct_db 到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'reduct_db', 'reduct_db'))

try:
    from reduct_db.db_config.safe_session import session_factory
    from reduct_db.db_dao.paper_dao import PaperDAO, PaperDetailDAO
    from reduct_db import test_connect
    DB_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入 reduct_db，卡片生成功能将被禁用: {e}")
    DB_AVAILABLE = False

from utils.logger import get_logger
from core.Card import ReductCard, splitSentence

logger = get_logger('card_generator')


class CardGenerator:
    """视频解说卡片生成器"""
    
    def __init__(self, storage_dir: str = None):
        """
        初始化卡片生成器
        
        Args:
            storage_dir: 卡片数据存储目录，默认为 ./cards
        """
        self.db_available = DB_AVAILABLE
        self.storage_dir = storage_dir or os.path.join(os.getcwd(), 'cards')
        
        # 确保存储目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
        if self.db_available:
            # 测试数据库连接
            if not test_connect():
                logger.error("数据库连接失败，卡片生成功能将被禁用")
                self.db_available = False
            else:
                logger.info("数据库连接成功，卡片生成器初始化完成")
        else:
            logger.warning("数据库不可用，卡片生成功能被禁用")
    
    def generate_card_from_arxiv_id(self, arxiv_id: str) -> Optional[ReductCard]:
        """
        根据 ArXiv ID 生成解说卡片
        
        Args:
            arxiv_id: ArXiv 论文ID，例如 "2024.12345" 或 "2024.12345v1"
        
        Returns:
            ReductCard: 生成的卡片对象，如果失败则返回 None
        """
        if not self.db_available:
            logger.error("数据库不可用，无法生成卡片")
            return None
        
        try:
            # 首先尝试原始ID，然后尝试清理后的ID
            clean_arxiv_id = self._clean_arxiv_id(arxiv_id)
            logger.info(f"开始为 ArXiv ID {arxiv_id} 生成解说卡片")
            
            # 创建数据库会话
            session = session_factory()
            paper_dao = PaperDAO(session)
            paper_detail_dao = PaperDetailDAO(session)
            
            try:
                # 1. 先尝试原始ID查询论文
                paper = paper_dao.get_by_external_id(arxiv_id)
                
                # 2. 如果没找到，尝试清理后的ID
                if not paper and clean_arxiv_id != arxiv_id:
                    paper = paper_dao.get_by_external_id(clean_arxiv_id)
                
                if not paper:
                    logger.warning(f"未找到 ArXiv ID {arxiv_id} 或 {clean_arxiv_id} 对应的论文")
                    return None
                
                logger.info(f"找到论文: {paper.title[:50]}...")
                
                # 3. 根据 paper_id 查询论文详情
                paper_detail = paper_detail_dao.get_by_paper_id(paper.id)
                
                if not paper_detail:
                    logger.warning(f"未找到论文 ID {paper.id} 的详细信息")
                    return None
                
                # 4. 检查是否有中文解说脚本
                if not paper_detail.cn_script:
                    logger.warning(f"论文 {arxiv_id} 没有可用的中文解说脚本")
                    return None
                
                # 5. 生成卡片（使用原始ID作为卡片ID，传入paper对象）
                card = self._create_card_from_paper_detail(arxiv_id, paper_detail, paper)
                
                logger.info(f"成功生成 ArXiv ID {arxiv_id} 的解说卡片")
                return card
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"生成卡片时发生错误: {e}")
            return None
    
    def save_card(self, card: ReductCard, target_dir: str = None, filename: str = None) -> str:
        """
        保存卡片到本地文件
        
        Args:
            card: 要保存的卡片对象
            target_dir: 目标目录，如果不指定则使用默认存储目录
            filename: 文件名，默认使用 {arXivID}.json
        
        Returns:
            str: 保存的文件路径
        """
        if filename is None:
            filename = f"{card.arXivID}.json"
        
        # 使用指定目录或默认目录
        save_dir = target_dir if target_dir else self.storage_dir
        os.makedirs(save_dir, exist_ok=True)
        
        filepath = os.path.join(save_dir, filename)
        
        # 将卡片转换为字典格式
        card_data = {
            'arXivID': card.arXivID,
            'info_CN': card.info_CN,
            'info_EN': card.info_EN,
            'created_at': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # 保存到JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(card_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"卡片已保存到: {filepath}")
        return filepath
    
    def load_card(self, arxiv_id: str) -> Optional[ReductCard]:
        """
        从本地文件加载卡片
        
        Args:
            arxiv_id: ArXiv ID
        
        Returns:
            ReductCard: 加载的卡片对象，如果文件不存在则返回 None
        """
        filename = f"{self._clean_arxiv_id(arxiv_id)}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                card_data = json.load(f)
            
            return ReductCard(
                arXivID=card_data['arXivID'],
                info_CN=card_data['info_CN'],
                info_EN=card_data['info_EN']
            )
        except Exception as e:
            logger.error(f"加载卡片文件 {filepath} 失败: {e}")
            return None
    
    def get_or_create_card(self, arxiv_id: str) -> Optional[ReductCard]:
        """
        获取或创建卡片（先尝试从本地加载，如果不存在则从数据库生成）
        
        Args:
            arxiv_id: ArXiv ID
        
        Returns:
            ReductCard: 卡片对象
        """
        # 先尝试从本地加载
        card = self.load_card(arxiv_id)
        if card:
            logger.info(f"从本地加载了 {arxiv_id} 的卡片")
            return card
        
        # 本地不存在，从数据库生成
        card = self.generate_card_from_arxiv_id(arxiv_id)
        if card:
            # 保存到本地
            self.save_card(card)
        
        return card
    
    def _clean_arxiv_id(self, arxiv_id: str) -> str:
        """
        清理 ArXiv ID，移除可能的前缀和版本号
        
        Args:
            arxiv_id: 原始 ArXiv ID
        
        Returns:
            str: 清理后的 ArXiv ID
        """
        # 移除可能的 URL 前缀
        if 'arxiv.org/abs/' in arxiv_id:
            arxiv_id = arxiv_id.split('arxiv.org/abs/')[-1]
        
        # 移除版本号 (例如 v1, v2)
        if 'v' in arxiv_id:
            arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
        
        return arxiv_id.strip()
    
    def _split_sentence(self, sentence: str, is_cn: bool = True) -> List[str]:
        """
        将长句子按标点符号分割成短句
        
        Args:
            sentence: 要分割的句子
            is_cn: 是否为中文（True为中文，False为英文）
        
        Returns:
            List[str]: 分割后的句子列表
        """
        import re
        
        if is_cn:
            # 中文按 ，。 分割
            res = re.split(r'[，。]', sentence)
        else:
            # 英文按 ,. 分割
            res = re.split(r'[,.]', sentence)
        
        # 移除空字符串
        res = [s.strip() for s in res if s.strip()]
        return res
    
    def _create_card_from_paper_detail(self, arxiv_id: str, paper_detail, paper) -> ReductCard:
        """
        从论文详情创建卡片对象
        
        Args:
            arxiv_id: ArXiv ID
            paper_detail: 论文详情对象
            paper: 论文主对象（用于获取日期信息）
        
        Returns:
            ReductCard: 创建的卡片对象
        """
        # 构建完整的语音内容
        info_cn = []
        
        # 添加中文介绍
        if paper_detail.cn_script:
            cn_sentences = self._split_sentence(paper_detail.cn_script, is_cn=True)
            info_cn.extend(cn_sentences)
        
        # 不再使用英文脚本
        info_en = []
        
        return ReductCard(
            arXivID=arxiv_id,
            info_CN=info_cn,
            info_EN=info_en
        )
    
    def list_saved_cards(self) -> List[str]:
        """
        列出所有已保存的卡片
        
        Returns:
            List[str]: ArXiv ID 列表
        """
        cards = []
        if os.path.exists(self.storage_dir):
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    arxiv_id = filename[:-5]  # 移除 .json 后缀
                    cards.append(arxiv_id)
        return cards


# 全局卡片生成器实例
card_generator = CardGenerator()


def generate_video_script_card(arxiv_id: str, target_dir: str = None) -> Optional[ReductCard]:
    """
    便捷函数：为指定的 ArXiv ID 生成视频解说卡片
    
    Args:
        arxiv_id: ArXiv 论文ID
        target_dir: 目标保存目录，如果指定则保存到该目录
    
    Returns:
        ReductCard: 生成的卡片对象
    """
    card = card_generator.get_or_create_card(arxiv_id)
    
    # 如果指定了目标目录，则保存到该目录
    if card and target_dir:
        try:
            saved_path = card_generator.save_card(card, target_dir)
            logger.info(f"卡片已保存到: {saved_path}")
        except Exception as e:
            logger.error(f"保存卡片到 {target_dir} 失败: {e}")
    
    return card
