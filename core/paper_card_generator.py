#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
论文卡片生成器
在视频下载完成后，根据 ArXiv ID 从 reduct_db 查询论文信息，生成标准化卡片格式
"""

import sys
import os
import json
from typing import Optional, List
from pathlib import Path
import re

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


class PaperCardGenerator:
    """论文卡片生成器，负责从数据库查询论文信息并生成卡片"""
    
    def __init__(self, cards_storage_dir: str = "cards_data"):
        """
        初始化卡片生成器
        
        Args:
            cards_storage_dir: 卡片数据存储目录
        """
        self.cards_storage_dir = Path(cards_storage_dir)
        self.cards_storage_dir.mkdir(exist_ok=True)
        
        self.db_available = DB_AVAILABLE
        if self.db_available:
            # 测试数据库连接
            if not test_connect():
                logger.error("数据库连接失败，卡片生成功能将被禁用")
                self.db_available = False
            else:
                logger.info("数据库连接成功，卡片生成器已就绪")
    
    def generate_card_for_paper(self, arxiv_id: str) -> Optional[ReductCard]:
        """
        根据 ArXiv ID 生成论文卡片
        
        Args:
            arxiv_id: ArXiv 论文 ID (例如: "2024.12345")
        
        Returns:
            ReductCard: 生成的卡片对象，如果失败则返回 None
        """
        if not self.db_available:
            logger.warning(f"数据库不可用，无法为论文 {arxiv_id} 生成卡片")
            return None
        
        try:
            session = session_factory()
            paper_dao = PaperDAO(session)
            paper_detail_dao = PaperDetailDAO(session)
            
            # 1. 根据 external_id (ArXiv ID) 查询论文
            paper = paper_dao.get_by_external_id(arxiv_id)
            if not paper:
                logger.warning(f"未找到 ArXiv ID 为 {arxiv_id} 的论文")
                return None
            
            # 2. 查询论文详情
            paper_detail = paper_detail_dao.get_by_paper_id(paper.id)
            if not paper_detail:
                logger.warning(f"论文 {arxiv_id} 缺少详细信息")
                return None
            
            # 3. 检查脚本是否存在
            if not paper_detail.cn_script and not paper_detail.eng_script:
                logger.warning(f"论文 {arxiv_id} 缺少解说脚本")
                return None
            
            # 4. 生成卡片
            card = ReductCard(
                arXivID=arxiv_id,
                info_CN=splitSentence(paper_detail.cn_script or ""),
                info_EN=splitSentence(paper_detail.eng_script or "", False)
            )
            
            logger.info(f"成功为论文 {arxiv_id} 生成卡片")
            return card
            
        except Exception as e:
            logger.error(f"为论文 {arxiv_id} 生成卡片时发生错误: {e}")
            return None
        finally:
            if 'session' in locals():
                session.close()
    
    def save_card(self, card: ReductCard) -> str:
        """
        保存卡片到本地文件
        
        Args:
            card: 要保存的卡片对象
        
        Returns:
            str: 保存的文件路径
        """
        card_file = self.cards_storage_dir / f"{card.arXivID}_card.json"
        
        card_data = {
            "arXivID": card.arXivID,
            "info_CN": card.info_CN,
            "info_EN": card.info_EN,
            "generated_at": str(Path(__file__).stat().st_mtime)
        }
        
        with open(card_file, 'w', encoding='utf-8') as f:
            json.dump(card_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"卡片已保存到: {card_file}")
        return str(card_file)
    
    def load_card(self, arxiv_id: str) -> Optional[ReductCard]:
        """
        从本地文件加载卡片
        
        Args:
            arxiv_id: ArXiv 论文 ID
        
        Returns:
            ReductCard: 加载的卡片对象，如果文件不存在则返回 None
        """
        card_file = self.cards_storage_dir / f"{arxiv_id}_card.json"
        
        if not card_file.exists():
            return None
        
        try:
            with open(card_file, 'r', encoding='utf-8') as f:
                card_data = json.load(f)
            
            card = ReductCard(
                arXivID=card_data["arXivID"],
                info_CN=card_data["info_CN"],
                info_EN=card_data["info_EN"]
            )
            
            logger.info(f"从文件加载卡片: {card_file}")
            return card
            
        except Exception as e:
            logger.error(f"加载卡片文件 {card_file} 失败: {e}")
            return None
    
    def generate_and_save_card(self, arxiv_id: str, force_regenerate: bool = False) -> Optional[str]:
        """
        生成并保存论文卡片（组合方法）
        
        Args:
            arxiv_id: ArXiv 论文 ID
            force_regenerate: 是否强制重新生成（忽略已存在的文件）
        
        Returns:
            str: 保存的文件路径，如果失败则返回 None
        """
        # 1. 检查是否已存在且不强制重新生成
        if not force_regenerate:
            existing_card = self.load_card(arxiv_id)
            if existing_card:
                logger.info(f"论文 {arxiv_id} 的卡片已存在，跳过生成")
                return str(self.cards_storage_dir / f"{arxiv_id}_card.json")
        
        # 2. 从数据库生成新卡片
        card = self.generate_card_for_paper(arxiv_id)
        if not card:
            return None
        
        # 3. 保存卡片
        return self.save_card(card)
    
    def batch_generate_cards(self, arxiv_ids: List[str], force_regenerate: bool = False) -> List[str]:
        """
        批量生成卡片
        
        Args:
            arxiv_ids: ArXiv ID 列表
            force_regenerate: 是否强制重新生成
        
        Returns:
            List[str]: 成功生成的卡片文件路径列表
        """
        successful_cards = []
        
        for arxiv_id in arxiv_ids:
            try:
                card_path = self.generate_and_save_card(arxiv_id, force_regenerate)
                if card_path:
                    successful_cards.append(card_path)
            except Exception as e:
                logger.error(f"批量生成卡片时处理 {arxiv_id} 失败: {e}")
        
        logger.info(f"批量生成完成: {len(successful_cards)}/{len(arxiv_ids)} 个卡片成功生成")
        return successful_cards
    
    def get_cards_for_video_generation(self, arxiv_ids: List[str]) -> List[ReductCard]:
        """
        获取用于视频生成的卡片列表
        
        Args:
            arxiv_ids: ArXiv ID 列表
        
        Returns:
            List[ReductCard]: 卡片对象列表
        """
        cards = []
        
        for arxiv_id in arxiv_ids:
            # 先尝试从文件加载
            card = self.load_card(arxiv_id)
            
            # 如果文件不存在，尝试从数据库生成
            if not card:
                card = self.generate_card_for_paper(arxiv_id)
                if card:
                    self.save_card(card)  # 保存到文件以便下次使用
            
            if card:
                cards.append(card)
            else:
                logger.warning(f"无法获取论文 {arxiv_id} 的卡片")
        
        return cards


# 创建全局卡片生成器实例
card_generator = PaperCardGenerator()


def generate_card_for_downloaded_paper(arxiv_id: str) -> Optional[str]:
    """
    为下载完成的论文生成卡片的便捷函数
    
    Args:
        arxiv_id: ArXiv 论文 ID
    
    Returns:
        str: 卡片文件路径，失败返回 None
    """
    return card_generator.generate_and_save_card(arxiv_id)
