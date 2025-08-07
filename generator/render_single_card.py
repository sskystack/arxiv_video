import numpy as np
import cv2

from tools.render_tool import capture_div_screenshot


def apply_tiled_watermark(image_path, output_path,
                          watermark_path=r'C:\Users\Ocean\Documents\GitHub\FamousCitesMe\DAP-demo-html\watermark.png',
                          scale=0.4, opacity=0.6, spacing=100):
    # 读取原始图像
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"Failed to read image {image_path}")
        return

    # 读取水印图像
    watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
    if watermark is None:
        print(f"Failed to read watermark {watermark_path}")
        return

    # 缩小水印图像
    h_wm, w_wm = watermark.shape[:2]
    watermark = cv2.resize(watermark, (int(w_wm * scale), int(h_wm * scale)), interpolation=cv2.INTER_AREA)

    # 获取图像和水印的尺寸
    h_img, w_img = image.shape[:2]
    h_wm, w_wm = watermark.shape[:2]

    # 提取水印的alpha通道并应用透明度
    if watermark.shape[2] == 4:
        alpha_wm = watermark[:, :, 3] / 255.0 * opacity
        watermark = watermark[:, :, :3]
    else:
        alpha_wm = np.ones((h_wm, w_wm)) * opacity

    # 创建包含alpha通道的水印图像
    alpha_img_wm = np.dstack([watermark, alpha_wm])

    # 以对角线方式平铺水印
    step_x, step_y = w_wm + spacing, h_wm + spacing  # 设置水印的间距
    for y in range(0, h_img, step_y):
        for x in range(0, w_img, step_x):
            # 检查水印是否超出图像边界
            if x + w_wm > w_img or y + h_wm > h_img:
                continue
            # 将水印添加到图像上
            overlay_image_with_alpha(image, alpha_img_wm, x_offset=x, y_offset=y)

    # 保存结果图像
    cv2.imwrite(output_path, image)
    print(f"Watermarked image saved as {output_path}")

def overlay_image_with_alpha(img, img_overlay, x_offset=0, y_offset=0):
    """在图像上添加带透明度的叠加层"""
    y1, y2 = y_offset, y_offset + img_overlay.shape[0]
    x1, x2 = x_offset, x_offset + img_overlay.shape[1]

    alpha_s = img_overlay[:, :, 3] / 255.0
    alpha_l = 1.0 - alpha_s

    for c in range(0, 3):
        img[y1:y2, x1:x2, c] = (alpha_s * img_overlay[:, :, c] + alpha_l * img[y1:y2, x1:x2, c])
def watermark_images_in_folder(folder_path, output_folder,
                               watermark_path=r'C:\Users\Ocean\Documents\GitHub\FamousCitesMe\logo-1.png',
                               scale=0.4, opacity=0.4):
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历文件夹中的所有.png文件
    for filename in os.listdir(folder_path):
        if filename.endswith('.png'):
            image_path = os.path.join(folder_path, filename)
            output_path = os.path.join(output_folder, filename)
            apply_tiled_watermark(image_path, output_path, watermark_path, scale, opacity)



from PIL import Image, ImageDraw, ImageFont


def add_text_watermark(image_path, output_path, text, position, opacity=128):
    with Image.open(image_path).convert("RGBA") as base:
        # 创建一个透明的文本图层
        txt = Image.new('RGBA', base.size, (255, 255, 255, 0))

        # 设置字体和大小
        fnt = ImageFont.load_default()
        d = ImageDraw.Draw(txt)

        # 绘制文本
        d.text(position, text, font=fnt, fill=(255, 255, 255, opacity))

        # 合并图层
        watermarked = Image.alpha_composite(base, txt)
        watermarked = watermarked.convert("RGB")  # 如果不需要透明背景
        watermarked.save(output_path)


# 使用示例

def get_subdirectories(path):
    """ 获取指定路径下所有子目录的路径 """
    subdirs = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    return subdirs



def main(args):
    # 获取文件名（无后缀）和目录路径
    folder_name = os.path.basename(args.html_dir)
    parent_dir = os.path.dirname(args.html_dir)
    folder_name = folder_name.split('_')[1]
    html_file_path = os.path.join(args.html_dir, f'{folder_name}.html')
    capture_div_screenshot(html_file_path, os.path.join(parent_dir, f'{folder_name}.png'))
    # add_text_watermark('path_to_your_image.jpg', 'output_image.jpg', 'Your Watermark', (10, 10))
    # apply_tiled_watermark(r'I:\arxiv\2024-7-11\7_d20c1be4-3a81-4768-8970-a2ba5605e5da.png', r'I:\arxiv\2024-7-11\watermark\7_d20c1be4-3a81-4768-8970-a2ba5605e5da.png', r'C:\Users\Ocean\Documents\GitHub\FamousCitesMe\logo-1.png', 0.4, 0.4)
def render_single_card(render_dir, external_id):
    html_file_path = os.path.join(render_dir, f'{external_id}.html')
    capture_div_screenshot(html_file_path,os.path.join(render_dir, f'{external_id}.png'))

import argparse
import os


# 定义事件处理器


if __name__ == '__main__':
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(
        description="Capture a screenshot of a div from HTML and save as PNG in the same directory.")

    # 添加参数
    parser.add_argument('--html_template_file', type=str, default='',help='The path to the HTML template file.')

    # 解析命令行参数
    args = parser.parse_args()
    args.html_dir = r'D:\arxiv\2025-5-6\0_2505.02018v1'
    # 执行 main 函数
    # main(args)
    #
    # for dir in get_subdirectories(r'D:\arxiv\2025-3-27'):
    #     print(dir)
    #     folder_name = os.path.basename(dir)
    #     parent_dir = os.path.dirname(dir)
    #     if os.path.exists(os.path.join(parent_dir, f'{folder_name}.png')):
    #         html_name = folder_name.split('_')[1]
    #         capture_div_screenshot(os.path.join(dir, f'{html_name}.html'), os.path.join(parent_dir, f'{folder_name}.png'))
    #     else:
    #         print(f'No HTML file found for {folder_name}')

    render_single_card(r'D:\arxiv\2025-7-21\2507.13332v1', '2507.13332v1')
