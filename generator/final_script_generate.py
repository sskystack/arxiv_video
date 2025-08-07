import glob
from pathlib import Path
import pypandoc
import shutil
import zipfile
import pandas as pd
from reduct_db.db_dao import PaperDAO
from reduct_db.db_config import use_session
from reduct_db.db_oss import upload_single_file
from cfg.safe_session import session_factory
from reduct_db.db_entities import Daily_Status, Papers
from database.oss_operator import upload_image
from db_services.misc_service import DailyStatusService
from tools.embedding_tool import encode_and_index, embed_papers_to_db
from tools.file_tool import write_string_to_file
from tools.html_tool import generate_HTML_template_LTS
from tools.sponser_msg_tool import parse_csv_from_file, print_in_chunks
from tools.render_tool import capture_div_screenshot
from cfg.STATUS import *
from reduct_db.db_dao import paper_dao
def get_arxiv_ids(dir_path):
    # 列出指定路径下所有的png和jpeg文件
    file_list = glob.glob(os.path.join(dir_path, '*.png')) + glob.glob(os.path.join(dir_path, '*.jpeg'))
    # 初始化arxivID列表
    arxiv_ids = []

    # 遍历文件列表，处理每个文件名
    for file_path in file_list:
        # 获取文件名（不包含路径）
        filename = os.path.basename(file_path)
        # 分割文件名，按照'_'分割
        parts = filename.split('_')
        # 假设arxivID总是在第二个位置（index_arxivID.png）
        if len(parts) > 1:
            arxiv_id = parts[1]
            arxiv_ids.append(arxiv_id.replace('.png', ''))

    return arxiv_ids

@use_session()
def get_arxiv_ids_from_db(session=None):
    papers = PaperDAO(session).list_by_multi_status_today([ResultStatus.COMPLETED_ALL,ResultStatus.REGENERATED,ResultStatus.SUCCESS])
    arxiv_ids = [paper.external_id for paper in papers]
    return arxiv_ids

def filter_csv(dir_path, db_enabled=True):
    # 构建CSV文件的路径和输出文件路径
    csv_path = os.path.join(dir_path, 'reading.csv')
    output_csv_path = os.path.join(dir_path, 'reading-filtered.csv')
    deprecated_csv_path = os.path.join(dir_path, 'reading-deprecated.csv')

    # 读取CSV文件
    df = pd.read_csv(csv_path)
    # 添加原始索引列 'ori_index'，记录每一行的原始位置
    df['ori_index'] = df.index
    # 如果'script'在列中，将其移至第一列
    if 'script' in df.columns:
        # 重新排序列，将'script'放在最前面
        cols = ['script'] + [col for col in df.columns if col != 'script']
        df = df[cols]
    # 调用之前定义的函数来获取arxiv_id列表
    if db_enabled:
        arxiv_ids = get_arxiv_ids_from_db()
    else:
        arxiv_ids = get_arxiv_ids(dir_path)
    # 过滤数据，保留列表中存在的arxiv_id
    filtered_df = df[df['arxiv_id'].isin(arxiv_ids)]
    # 重新排序列
    priority_columns = ['oa_access','script']
    other_columns = [col for col in filtered_df.columns if col not in priority_columns]
    filtered_df = filtered_df[priority_columns + other_columns]
    filtered_df.to_csv(output_csv_path, index=False, )
    # 找出并保存被删除的行
    deprecated_df = df[~df['arxiv_id'].isin(arxiv_ids)]
    # 同样使用utf-8-sig编码保存被删除的行
    deprecated_df.to_csv(deprecated_csv_path, index=False, )


def generate_md_docx(csv_path: str, total):
    # 读取CSV文件
    df = pd.read_csv(csv_path)
    row_count = df.shape[0]
    # 确保 'author_cites' 列是数值类型
    df['author_cites'] = pd.to_numeric(df['author_cites'], errors='coerce')

    df['cluster_id'] = df['cluster_id'].astype(int)  # 确保 cluster_id 是整数
    df = df.sort_values(by=['cluster_id', 'combined_score'], ascending=[True, False])

    df['final_index'] = range(0, len(df))
    df.to_csv(csv_path, index=False, encoding='utf-8')

    # 遍历数据框并重命名文件
    for _, row in df.iterrows():
        old_name = f"{row['ori_index']}_{row['arxiv_id']}.png"
        new_name = f"{row['final_index']}_{row['ori_index']}_{row['arxiv_id']}.png"

        old_path = os.path.join(arXiv_analysis_dir, old_name)
        new_path = os.path.join(arXiv_analysis_dir, new_name)

        # 检查文件是否存在，避免错误
        if os.path.exists(old_path):
            try:
                os.rename(old_path, new_path)
            except FileExistsError:
                os.remove(new_path)
                os.rename(old_path, new_path)
            print(f"Renamed: {old_name} -> {new_name}")
        else:
            print(f"File not found: {old_name}")


    # 生成Markdown文件路径
    md_path = csv_path.replace('.csv', '.md')
    session = session_factory()
    ds = session.query(Daily_Status).filter(Daily_Status.date_id == f'{y}-{m}-{d}').first()
    published_arxiv_ids = []


    with open(md_path, 'w', encoding='utf-8') as md_file:
        md_file.write(
            f'### {y}年{m}月{d}日arXiv 计算机视觉方向发文共{total}篇，减论Agent通过算法为您推荐。\n\n') # 在玻尔首页输入感兴趣的论文标题，即可一键开启AI精读，轻松掌握核心内容。
        for i, (_, row) in enumerate(df.iterrows()):
            published_arxiv_ids.append(row['arxiv_id'])
            md_file.write(f"## arXiv ID: {row['final_index'] }_{row['ori_index']}_{row['arxiv_id']} -- ClusterID: {row['cluster_id']} -- Overall Rating: {row['combined_score']}\n")
            md_file.write(f"- {row['script']}\n")
            title = row['title']
            arxiv_link = f"{row['arxiv_id']}" if pd.notna(row['arxiv_id']) else "N/A"
            github_link = f"{row['oa_access']}" if pd.notna(row['oa_access']) else "N/A"
            sponser_link = f"{row['shortUrl']}" if pd.notna(row['shortUrl']) else "N/A"
            md_file.write(f"【Bohr精读】\n{sponser_link}\n")
            md_file.write(f"【arXiv链接】\nhttp://arxiv.org/abs/{arxiv_link}\n")
            md_file.write(f"【代码地址】\n{github_link}\n")
            md_file.write(f"【ENG Script】\n{row['ENG_script']}\n")
            md_file.write(
                f"- Meta Info: 《{title}》| Author Cites: {row['author_cites']} | TNCSI: {row['TNCSI']} | Cites_norm: {row['log_cites_normalized']} | TNCSI_norm: {row['TNCSI_normalized']} \n\n\n\n")
        md_file.write('欢迎关注减论，用科技链接个体。\n')
        parsed_result = parse_csv_from_file(os.path.join(arXiv_analysis_dir, 'reading-filtered.csv'))
        sponser_msg = print_in_chunks(parsed_result)
        md_file.write(sponser_msg)
    if ds:
        ds.published_arxiv_ids = str(published_arxiv_ids)
        session.commit()
    # 生成Markdown文件路径
    temp_md_path = csv_path.replace('.csv', '-docx.md')

    # 写入Markdown文件
    with open(temp_md_path, 'w', encoding='utf-8') as md_file:
        md_file.write(
            f'### {y}年{m}月{d}日arXiv cs.CV发文量约{total}余篇，减论Agent通过算法为您推荐。\n\n')# 在玻尔首页输入感兴趣的论文标题，即可一键开启AI精读，轻松掌握核心内容。
        CP_path = f'''{os.path.join(os.path.dirname(csv_path), 'cover_page.png')}'''
        md_file.write(f'''![]({CP_path})\n\n''')
        for i, (_, row) in enumerate(df.iterrows()):
            img_pth = f'''{row['final_index'] }_{row['ori_index']}_{row['arxiv_id']}.png'''
            abs_img_path = f'''{os.path.join(os.path.dirname(csv_path), img_pth)}'''
            md_file.write(f'''![]({abs_img_path})\n\n''')
            md_file.write(f"{row['script']}\n\n")
            arxiv_link = f"{row['arxiv_id']}" if pd.notna(row['arxiv_id']) else "N/A"
            github_link = f"{row['oa_access']}" if pd.notna(row['oa_access']) else "N/A"
            sponser_link = f"{row['shortUrl']}" if pd.notna(row['shortUrl']) else "N/A"
            # md_file.write(
            #     f'<a href="{sponser_link}" style="color: #1A0DB2; text-decoration: none;">{sponser_link}</a>\n\n')
            md_file.write(f"【Bohr精读】\n\n{sponser_link}\n\n")
            md_file.write(f"【arXiv链接】\n\nhttp://arxiv.org/abs/{arxiv_link}\n\n")
            md_file.write(f"【代码地址】\n\n{github_link}\n\n\n\n")
            # md_file.write(f"{sponser_link}\n\n")
            # md_file.write(f"http://arxiv.org/abs/{arxiv_link}\n\n")
            # md_file.write(f"{github_link}\n\n\n\n")
        end_img_path = f'''{os.path.join(os.path.dirname(csv_path), 'end_page.png')}'''
        md_file.write(f'''![]({end_img_path})\n\n''')
        md_file.write('欢迎关注减论，用科技链接个体。\n\n')

    # with open(temp_md_path, 'r', encoding='utf-8') as md_file:
    #     markdown_text = md_file.read()
    # html_content = markdown.markdown(markdown_text)
    #
    # # 将生成的 HTML 内容写入文件
    # html_path =  temp_md_path.replace('-docx.md', '.html')  # 替换为你想要保存的路径
    #
    # with open(html_path, 'w', encoding='utf-8') as file:
    #     file.write(html_content)


def organize_and_compress_files(src_dir):
    # 获取今天的日期，格式为MM-DD
    today = now.strftime("%m-%d")

    # 在源目录下创建以今天日期命名的文件夹
    destination_dir = os.path.join(src_dir, today)
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # 删除src_dir下名为trend.png和word_cloud.png的文件
    for file_name in ['trend.png', 'word_cloud.png']:
        file_path = os.path.join(src_dir, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    #

    # 定义要移动的文件类型和特定文件
    file_types = ('*.png', '*.jpeg')
    specific_files = ('reading-filtered.md', 'reading.docx')

    # 查找并移动所有图片文件
    for file_type in file_types:
        for file in glob.glob(os.path.join(src_dir, file_type)):
            shutil.move(file, destination_dir)

    # 查找并移动特定文件
    for file_name in specific_files:
        file_path = os.path.join(src_dir, file_name)
        if os.path.exists(file_path):
            shutil.move(file_path, destination_dir)

    # 创建压缩文件（ZIP）
    zip_filename = os.path.join(src_dir, f"{today}.zip")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(destination_dir):
            for file in files:
                zipf.write(os.path.join(root, file),os.path.relpath(os.path.join(root, file), os.path.join(destination_dir, '..')))

    print(f"压缩成功")

from docx import Document
from docx.shared import RGBColor


def set_custom_blue_color_for_text(doc_path):
    # 加载文档
    doc = Document(doc_path)

    # 定义特定的蓝色
    custom_blue = RGBColor(0x1A, 0x0D, 0xAB)  # 十六进制颜色1A0DAB转换为RGB

    # 遍历每个段落
    for paragraph in doc.paragraphs:
        if '【Bohr精读】' in paragraph.text:
            # 更改段落中所有字体的颜色
            for run in paragraph.runs:
                run.font.color.rgb = custom_blue
        if 'j1q.cn' in paragraph.text:
            # 更改段落中所有字体的颜色
            for run in paragraph.runs:
                run.font.color.rgb = custom_blue

    # 保存修改后的文档
    doc.save(doc_path)


def update_csv_from_db(csv_path):
    """
    根据数据库中数据更新 CSV 文件中的 oa_access 和 script 字段。
    如果记录的 valid 值不是 200，则从 CSV 中删除该行。

    :param csv_path: CSV 文件路径
    """
    # 读取 CSV 文件
    csv_data = pd.read_csv(csv_path)

    try:
        # 尝试创建数据库会话
        session = session_factory()
        print("数据库连接成功，开始更新 CSV 文件...")

        # 遍历 CSV 文件中的每一行
        rows_to_keep = []  # 用于保存需要保留的行索引

        for index, row in csv_data.iterrows():
            # 根据 arxiv_id 查询数据库
            # record = session.query(Papers).filter(Papers.external_id == row['arxiv_id']).first()
            # if record and record.valid//100 == 2:
            record = session.query(Papers).filter(
                Papers.external_id == row['arxiv_id'],
                Papers.valid.in_([ResultStatus.COMPLETED_ALL, ResultStatus.SUCCESS, ResultStatus.REGENERATED])
            ).first()
            if record:
                # 更新 CSV 中的字段
                csv_data.at[index, 'oa_access'] = record.paper_detail.code_url  # 假设数据库字段名为 oa
                csv_data.at[index, 'script'] = record.paper_detail.cn_script  # 假设数据库字段名为 script
                rows_to_keep.append(index)  # 记录需要保留的行索引

                # print(f"删除记录：arxiv_id={row['arxiv_id']}（valid 不为 200）")

        # 仅保留需要的行
        csv_data = csv_data.loc[rows_to_keep]

        # 保存更新后的 CSV 文件
        csv_data.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"CSV 文件已成功更新：{csv_path}")

    except Exception as e:
        print(f"更新失败：{e}")

    finally:
        # 关闭数据库会话（如果存在）
        if 'session' in locals():
            session.close()
        else:
            print("未连接到数据库，保留原始 CSV 文件内容。")



from bs4 import BeautifulSoup



@use_session()
def replace_oa_addr_html(html_path, paper_id, session=None):
    """
    读取指定路径的 HTML 文件并将 class 为 'oa' 的 span 标签内容
    和 class 为 'location' 的 div 内容替换为新的地址和简介文字。

    Args:
        html_path (str): HTML 文件路径。
        paper_detail: 包含 code_url 和 cn_script 属性的对象。
    """
    # 读取 HTML 文件内容
    paper = PaperDAO(session).get_by_id(paper_id)
    html_content = None
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError as fnfe:
        print(fnfe)
        html = generate_HTML_template_LTS(paper.external_id)
        if html:
            html_file = os.path.join(os.path.join(arXiv_analysis_dir, f'{paper.paper_detail.ori_index}_{paper.external_id}'),
                                     f"{paper.external_id}.html")
            write_string_to_file(html, html_file)
            # capture_div_screenshot(
            #     html_file,
            #     os.path.join(arXiv_analysis_dir, f"{paper_detail.ori_index}_{external_id}.png")
            # )


    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 替换 oa 链接
    oa_span = soup.find('span', class_='oa')
    if oa_span:
        oa_span.string = paper.paper_detail.code_url
    else:
        print("未找到 class 为 'oa' 的 span 标签。")

    # 替换 location 中文介绍
    location_div = soup.find('div', class_='location')
    if location_div:
        location_div.string = paper.paper_detail.cn_script
    else:
        print("未找到 class 为 'location' 的 div 标签。")

    # 保存修改后的 HTML
    with open(html_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))

    print("地址和介绍替换完成！")

@use_session()
def upload_paper_images(paper: Papers, card_image_pth: str, fig_tab_dir: str, cover_page_pth:str=None,session=None):
    """
    上传卡片图 + 图表图到 OSS，并将 paper.is_ready 设置为 1

    参数:
    - paper: Papers ORM 对象，必须含 paper.guid
    - card_image_pth: 本地卡片图路径
    - fig_tab_dir: 本地图表图目录，上传所有 .jpg 文件
    """
    # 获取 guid 和卡片图扩展名
    if paper.is_ready:
        return  # 已经上传过了，不用重复上传
    try:
        if cover_page_pth:
            ext = Path(cover_page_pth).suffix.lower()  # 获取扩展名，例如 .jpg
            dir_name = Path(cover_page_pth).parent.name
            oss_cover_path = f"temp_cover/{dir_name}{ext}"
            upload_single_file(card_image_pth, oss_cover_path)
        paper_guid = paper.guid
        if card_image_pth:
            ext = Path(card_image_pth).suffix.lower()  # 获取扩展名，例如 .jpg
            oss_card_path = f"resource/{paper_guid}/{paper_guid}{ext}"
            upload_single_file(card_image_pth, oss_card_path)

        # 上传 fig_tab_dir 下所有 .jpg 图表图
        for filename in os.listdir(fig_tab_dir):
            if filename.lower().endswith(".jpg"):
                local_path = os.path.join(fig_tab_dir, filename)
                oss_path = f"resource/{paper_guid}/{filename}"
                upload_single_file(local_path, oss_path)
    except Exception as e:
        print(e)
        return
    # 更新数据库状态
    dao = PaperDAO(session)
    paper = dao.get_by_id(paper.id)
    paper.is_ready = 1
    if paper.paper_detail.key_fig_name:
        paper.paper_detail.key_fig_url = f'https://image.reduct.cn/resource/{paper.guid}/{paper.paper_detail.key_fig_name}.jpg'
    if paper.paper_detail.key_tab_name:
        paper.paper_detail.key_tab_url = f'https://image.reduct.cn/resource/{paper.guid}/{paper.paper_detail.key_tab_name}.jpg'
    session.commit()
    print(f"✅ Paper {paper.id} 图片上传完成，已设置 is_ready = 1")

@use_session()
def final_genrate(session=None):

    use_db = True
    ds_entry = None
    try:
        ds_entry = session.query(Daily_Status).filter(Daily_Status.date_id == daily_str).first()
    except Exception as e:
        use_db = False
    if use_db:

        total = ds_entry.daily_pub_num  # len(aid)

        cur_dir = arXiv_analysis_dir
        arxiv_ids = get_arxiv_ids(cur_dir)
        reading_filtered_csv_path = os.path.join(cur_dir, 'reading-filtered.csv')
        md_path = os.path.join(cur_dir, 'reading-filtered-docx.md')
        docx_path = os.path.join(cur_dir, 'reading.docx')

        shutil.copyfile('../deprecated_code/end_page.png', os.path.join(cur_dir, 'end_page.png'))
        # 该操作根据cur_dir中的文件生成reading-filtered.csv
        filter_csv(cur_dir, db_enabled=True)
        # 该操作仅同步信息 数据库->CSV
        update_csv_from_db(os.path.join(cur_dir, 'reading-filtered.csv'))



        # from database.DB_Util import current_day_data

        paper_dao = PaperDAO(session)


        papers = paper_dao.list_by_multi_status_today([ResultStatus.REGENERATED]) #current_day_data(ID=ResultStatus.REGENERATED,) # date=datetime.datetime(2025, 1, 10)
        for paper in papers:
            paper = PaperDAO(session).get_by_id(paper.id)
            order_arxiv_id = f'{paper.paper_detail.ori_index}_{paper.external_id}'
            order_arxiv_id_dir = os.path.join(arXiv_analysis_dir, order_arxiv_id)
            order_html_path = os.path.join(order_arxiv_id_dir, f'{paper.external_id}.html')
            replace_oa_addr_html(order_html_path, paper.id)
            capture_div_screenshot(order_html_path, os.path.join(arXiv_analysis_dir, f'{order_arxiv_id}.png'))
            paper.valid = ResultStatus.COMPLETED_ALL
            session.flush()

        # trending_service = TrendingService(session)
        # 上传到oss
        cur_papers = paper_dao.list_by_multi_status_today([ResultStatus.COMPLETED_ALL, ResultStatus.SUCCESS, ResultStatus.REGENERATED, FilterReason.MANUAL, FilterReason.GENERIC, FilterReason.NO_OA])
        ids = [p.id for p in cur_papers]
        for paper in cur_papers:
            try:
                paper = session.query(Papers).filter_by(id=paper.id).first()
                if paper.valid in [ResultStatus.COMPLETED_ALL, ResultStatus.SUCCESS, ResultStatus.REGENERATED]:
                    order_arxiv_id = f'{paper.paper_detail.ori_index}_{paper.external_id}'
                    # 传主图给大创
                    upload_image(os.path.join(arXiv_analysis_dir, f'{order_arxiv_id}.png'), f'article/material/{str(paper.id)}-{str(paper.external_id)}/{paper.id}.png')
                    # 传主图给减论Agent-雨萌,并设置is_ready=1 # 要加入非常严格的校验 确保 真的ready了再设置
                    upload_paper_images(paper, os.path.join(arXiv_analysis_dir, f'{order_arxiv_id}.png'), fr"D:\reduct\paper_material\{paper.id}_{paper.external_id}")
                else:
                    upload_paper_images(paper, card_image_pth=None, fig_tab_dir=fr"D:\reduct\paper_material\{paper.id}_{paper.external_id}")

                # trending_service.create_from_paper_id(paper.id)
            except Exception as e:

                raise e
                # paper.valid = ErrorCode.UPLOAD_ERROR
            session.commit()



        # 写mysql embedding
        embed_papers_to_db(ids)
        # 发送通知
        print(ids)
        DS_service = DailyStatusService(session=session_factory())
        batch_size = 50
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            DS_service.send_papers(batch)

        generate_md_docx(reading_filtered_csv_path, total)

        output = pypandoc.convert_file(md_path, 'docx', outputfile=docx_path)

        print(f"转换成功")

        set_custom_blue_color_for_text(docx_path)
        print(f"染色成功")

        organize_and_compress_files(cur_dir)
    else:

        total = input("请输入今日发表的论文数量：")

        cur_dir = arXiv_analysis_dir
        # arxiv_ids = get_arxiv_ids(cur_dir)

        reading_filtered_csv_path = os.path.join(cur_dir, 'reading-filtered.csv')

        md_path = os.path.join(cur_dir, 'reading-filtered-docx.md')
        # 替换为实际的 Markdown 文件路径
        docx_path = os.path.join(cur_dir, 'reading.docx')
        #
        filter_csv(cur_dir, db_enabled=False)

        input(f'已生成{reading_filtered_csv_path}, 请检查该文件,若无问题,键入任意字符以继续：')

        generate_md_docx(reading_filtered_csv_path, total)

        output = pypandoc.convert_file(md_path, 'docx', outputfile=docx_path)

        print(f"转换成功")

        set_custom_blue_color_for_text(docx_path)
        print(f"染色成功")

        organize_and_compress_files(cur_dir)
    session.close()

if __name__ == '__main__':
    final_genrate()