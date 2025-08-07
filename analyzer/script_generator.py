import csv

import pandas as pd

from cfg.STATUS import *
from cfg.safe_session import use_session
from reduct_db.db_entities import Papers, Daily_Status, safe_str
from sqlalchemy import func

from generator.gpt4generate import generate_reading_script
from concurrent.futures import ThreadPoolExecutor, as_completed


from deprecated_code.title_traslator import oa_decode
from tools.markdown_tool import generate_markdown_from_csv


# @use_session()  # 主查询不需要提交
# def generate_script_markdown(session=None):
#     os.makedirs(arXiv_analysis_dir, exist_ok=True)
#     csv_path = os.path.join(arXiv_analysis_dir, 'reading.csv')
#     results = session.query(Papers) \
#         .filter(Papers.valid == TaskStatus.TO_SCRIPT_GENERATION, func.date(Papers.download_date) == now.date()) \
#         .all()
#     daily_status = session.query(Daily_Status).filter(
#         Daily_Status.date_id == daily_str
#     ).first()
#     arxiv_ids = [paper.external_id for paper in results]
#     print(f"Found {len(arxiv_ids)} papers to process.")
#
#     with ThreadPoolExecutor(max_workers=8) as executor:
#         futures = [executor.submit(process_single_paper, arxiv_id) for arxiv_id in arxiv_ids]
#         for future in as_completed(futures):
#             try:
#                 future.result()
#             except Exception as e:
#                 print(f"[ERROR] {e}")
#     results = session.query(Papers).filter(Papers.valid == TaskStatus.TO_CARD_GENERATION, func.date(Papers.download_date) == now.date()).all()
#     for paper in results:
#         with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
#             fieldnames = ['oa_access', 'script', 'author_cites', 'arxiv_id', 'title', 'abstract', 'TNCSI', 'shortUrl',
#                           'cluster_id', 'idLiterature', 'university', 'idea', 'ENG_script', ]
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#
#             if csvfile.tell() == 0:
#                 writer.writeheader()
#
#             writer.writerow({
#                 'oa_access': oa_decode(paper.paper_detail.code_url),
#                 'script': paper.paper_detail.cn_script,
#                 'author_cites': paper.paper_detail.author_cites_w_strategy,
#                 'arxiv_id': paper.external_id,
#                 'title': paper.title,
#                 'abstract': paper.paper_detail.abstract.strip().replace('\n', ' '),
#                 'TNCSI': paper.TNCSI,
#                 'shortUrl': paper.paper_detail.shortUrl,
#                 'cluster_id': paper.paper_detail.cluster_id,
#                 'idLiterature': paper.id,
#                 'university': paper.paper_detail.cn_university,
#                 'idea': paper.paper_detail.cn_idea,
#                 'ENG_script': paper.paper_detail.eng_script
#             })
#         session.flush()
#         # === 去重 CSV ===
#         df = pd.read_csv(csv_path)
#         df_unique = df.drop_duplicates(subset=['arxiv_id'], keep='first')
#         df_unique.to_csv(csv_path, index=False, encoding='utf-8')
#
#
#
#
#
#     generate_markdown_from_csv(csv_path, daily_status.daily_pub_num)

@use_session()
def process_single_paper(arxiv_id, session=None):
    paper = session.query(Papers).filter_by(external_id=arxiv_id).first()
    if not paper:
        print(f"{arxiv_id} not found.")
        return

    paper = session.merge(paper)
    print(f'Processing {paper.external_id}')

    if not os.path.exists(os.path.join(arXiv_analysis_dir, f'{paper.external_id}.pdf')):
        paper.valid = ErrorCode.PDF_NOT_FOUND
        print(f'PDF not exist. SKIPPING.')
        session.flush()
        return

    if paper.paper_detail.code_url is None or paper.paper_detail.code_url == '[]':
        if not paper.whitelisted:
            print(f'{paper.external_id} has NO OA CODE.')
            paper.valid = FilterReason.NO_OA
            session.flush()
            return

    author_cites = paper.paper_detail.author_cites_w_strategy
    reading_script_dict = generate_reading_script(paper.paper_detail)

    paper.paper_detail.author_cites_w_strategy = author_cites
    paper.paper_detail.cn_university = reading_script_dict['university']
    paper.paper_detail.cn_idea = reading_script_dict['idea']
    paper.paper_detail.cn_script = reading_script_dict['script']
    paper.paper_detail.eng_script = safe_str(reading_script_dict['ENG_script'], max_length=511)
    paper.valid = TaskStatus.TO_CARD_GENERATION
    session.flush()


