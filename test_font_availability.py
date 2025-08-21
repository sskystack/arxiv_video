#!/usr/bin/env python3
"""
测试字体可用性和字幕显示
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_font_availability():
    """测试不同字体的可用性"""
    logger.info("🔤 开始测试字体可用性")
    
    test_text = "测试中文字幕显示 Test English Display"
    
    # 测试的字体配置
    font_configs = [
        {"name": "SimHei", "type": "字体名称"},
        {"name": "/System/Library/Fonts/PingFang.ttc", "type": "系统字体文件"},
        {"name": "/Library/Fonts/Arial Unicode.ttf", "type": "Arial Unicode"},
        {"name": "/System/Library/Fonts/STHeiti Light.ttc", "type": "华文黑体"},
        {"name": "Arial", "type": "Arial字体"},
        {"name": "Helvetica", "type": "Helvetica字体"},
    ]
    
    successful_fonts = []
    
    for config in font_configs:
        font_name = config["name"]
        font_type = config["type"]
        
        try:
            logger.info(f"🧪 测试 {font_type}: {font_name}")
            
            # 尝试创建TextClip
            text_clip = TextClip(
                test_text,
                fontsize=40,
                color='black',
                font=font_name,
                align='center'
            )
            
            # 如果能获取大小，说明字体可用
            size = text_clip.size
            logger.info(f"  ✅ 成功 - 文本大小: {size}")
            successful_fonts.append(config)
            
            # 清理资源
            text_clip.close()
            
        except Exception as e:
            logger.error(f"  ❌ 失败: {str(e)}")
    
    logger.info(f"\n📊 字体测试结果:")
    logger.info(f"成功的字体数量: {len(successful_fonts)}")
    
    if successful_fonts:
        logger.info("可用字体列表:")
        for i, config in enumerate(successful_fonts):
            logger.info(f"  {i+1}. {config['type']}: {config['name']}")
        
        # 推荐最佳字体
        best_font = successful_fonts[0]
        logger.info(f"\n🎯 推荐使用: {best_font['type']} ({best_font['name']})")
        return best_font['name']
    else:
        logger.error("❌ 没有找到可用的字体！")
        return None

def test_subtitle_generation(font_name):
    """测试字幕生成"""
    if not font_name:
        logger.error("❌ 没有可用字体，跳过字幕生成测试")
        return
    
    logger.info(f"🎬 使用字体 {font_name} 测试字幕生成")
    
    test_sentences = [
        "2025年8月21日arXiv,cs.CV,发文量约97篇",
        "The Tsinghua University proposed a method",
        "该方法显著提升了模型性能"
    ]
    
    output_dir = Path("/tmp/test_font_subtitle")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, sentence in enumerate(test_sentences):
        try:
            logger.info(f"📝 测试句子 {i+1}: '{sentence}'")
            
            # 创建字幕文本
            text_clip = TextClip(
                sentence,
                fontsize=50,
                color='black',
                font=font_name,
                align='center'
            ).set_duration(3).set_start(i * 3)
            
            # 创建背景
            bgcolor_clip = ColorClip(
                size=text_clip.size,
                color=(250, 250, 210, 200),
                ismask=False
            ).set_duration(3).set_start(i * 3)
            
            # 合并
            subtitle_clip = CompositeVideoClip([bgcolor_clip, text_clip])
            
            logger.info(f"  ✅ 字幕片段 {i+1} 创建成功，大小: {text_clip.size}")
            
            # 清理资源
            text_clip.close()
            bgcolor_clip.close()
            subtitle_clip.close()
            
        except Exception as e:
            logger.error(f"  ❌ 字幕片段 {i+1} 创建失败: {str(e)}")

if __name__ == "__main__":
    # 测试字体可用性
    best_font = test_font_availability()
    
    # 测试字幕生成
    test_subtitle_generation(best_font)
