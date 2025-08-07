import logging
import os
from datetime import datetime

# 创建日志目录
log_dir = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 创建arxiv_logger
arxiv_logger = logging.getLogger('arxiv_video_crawler')
arxiv_logger.setLevel(logging.INFO)

# 创建文件处理器
log_filename = f"arxiv_video_{datetime.now().strftime('%Y_%m_%d')}.log"
log_filepath = os.path.join(log_dir, log_filename)
file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 设置格式
formatter = logging.Formatter(log_format)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器到logger
if not arxiv_logger.handlers:  # 避免重复添加处理器
    arxiv_logger.addHandler(file_handler)
    arxiv_logger.addHandler(console_handler)
