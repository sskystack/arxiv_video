import os
import shutil
import re

def rename_and_copy_png_files(source_folder, target_folder):
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)  # 如果目标文件夹不存在，则创建

    for filename in os.listdir(source_folder):
        if filename.lower().endswith(".png"):
            match = re.match(r"^(\d+)_([\d\w\.]+\.png)$", filename)
            if match:

                new_filename = match.group(2)  # 获取去掉X的文件名 (Y_Z.png)
                source_path = os.path.join(source_folder, filename)
                target_path = os.path.join(target_folder, new_filename)

                # 复制文件
                shutil.copy2(source_path, target_path)
                print(f"Copied: {filename} -> {new_filename}")

# 使用示例：
source_directory = r"D:\arxiv\2025-2-17\02-17"  # 替换为实际文件夹路径
target_directory = r"D:\arxiv\2025-2-17"  # 替换为目标文件夹路径

rename_and_copy_png_files(source_directory, target_directory)
