from sqlalchemy import func
import json
import time
import requests_cache
from langchain_core.exceptions import OutputParserException
from analyzer.llm_function import judge_key_figure, judge_key_table, single_paper_info_extract, get_key_idea
from analyzer.parser import paper_info_parser
from cfg.safe_session import session_factory, use_session
from crawler.bohrium_url import get_short_url

from reduct_db.db_entities import Papers
from logs.loggers import arxiv_logger
# 配置 requests_cache，使用 SQLite 后端
requests_cache.install_cache('demo_cache')
from cfg.STATUS import *
from langchain.output_parsers import OutputFixingParser
import langchain
from concurrent.futures import as_completed
langchain.debug = False
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from concurrent.futures import ThreadPoolExecutor
from langchain_community.chat_models import ChatOpenAI
from tqdm import tqdm
@use_session()
def process_paper_lpqa(arxiv_id, session=None):
    try:
        paper = session.query(Papers).filter(Papers.external_id == arxiv_id).first()
        if not paper:
            return f"Skipping process_paper({arxiv_id}). Maybe due to it has already been processed."

        arxiv_logger.info(f'Processing paper id: {paper.external_id}; title: {paper.title}')
        pdf_pth = os.path.join(arXiv_analysis_dir, paper.external_id+'.pdf')
        if not os.path.exists(pdf_pth):
            arxiv_logger.warning(f'{pdf_pth} does not exist. Skipping.')
            paper.valid = ErrorCode.PDF_NOT_FOUND
            return f'PDF not found {arxiv_id}'

        if paper.paper_detail.raw_resp is None:
            lpqa = single_paper_info_extract(abstract = paper.paper_detail.abstract,pdf_pth=pdf_pth,default_model=low_llm)
            paper.paper_detail.raw_resp = json.dumps(lpqa.__dict__, indent=0)
            session.flush()
            arxiv_logger.info(f'Saving {low_llm} response to the database...')
        else:
            arxiv_logger.info(f'Processing the existing paper DB')

            try:
                lpqa = paper_info_parser.parse(paper.paper_detail.raw_resp)
            except OutputParserException as e:

                arxiv_logger.warning(f'Response in DB parse error. Fixing with GPT4o')
                fix_parser = OutputFixingParser.from_llm(parser=paper_info_parser,llm=ChatOpenAI(model_name=low_llm, temperature=0))
                try:
                    lpqa = fix_parser.parse(paper.paper_detail.raw_resp)
                    paper.paper_detail.raw_resp = json.dumps(lpqa.__dict__, indent=0)
                except OutputParserException as e:
                    arxiv_logger.warning(f'Fix try again. Return')
                    paper.valid = ErrorCode.PARSER_ERROR
                    session.flush()

                    return f'GPT Parser Error for: {arxiv_id}'



        paper.paper_detail.key_idea = lpqa.IDEA
        paper.paper_detail.fig_caps = json.dumps(lpqa.FIGURE_CAPTION)
        paper.paper_detail.tab_caps = json.dumps(lpqa.TABLE_CAPTION)

        arxiv_logger.info(f'Judging key figure and table')
        paper.paper_detail.key_fig = judge_key_figure(lpqa)
        paper.paper_detail.key_tab = judge_key_table(lpqa)
        paper.valid = TaskStatus.TO_CLUSTER
        session.add(paper)  # 将修改后的对象标记为需要保存的对象
        session.flush()


    except Exception as e:
        arxiv_logger.error(f"Error processing paper id {arxiv_id} in process paper: {e}")
        return f'Something wrong in processing Paper id {arxiv_id}'
    finally:
        return f'Paper id {arxiv_id} processed successfully.'

from pathlib import Path




@use_session()
def extract_key_fig(arxiv_id, session=None):
    try:
        paper = session.query(Papers).filter(Papers.external_id == arxiv_id).first()
        content_list_json_pth = os.path.join(os.path.join(daily_imgs_dir, f'{paper.id}_{paper.external_id}'),f'{paper.id}_{paper.external_id}_content_list.json')
        if not os.path.exists(content_list_json_pth):
            arxiv_logger.warning(f'{content_list_json_pth} does not exist. Skipping extract')
            paper.valid = ErrorCode.PDF_NOT_FOUND
            return f'PDF not found {arxiv_id}'
        with open(content_list_json_pth, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        if json_data is None:
            paper.valid = ErrorCode.PARSE_RESULT_NOT_FOUND
            return f'Something wrong in processing Paper id {arxiv_id}'

        fig_tab_dict = get_figs_tabs_LTS(json_data)
        paper.paper_detail.fig_caps = json.dumps(fig_tab_dict.get("figs", []))
        paper.paper_detail.key_fig = judge_key_figure(fig_tab_dict.get("figs", []))
        paper.paper_detail.key_fig_name = get_img_path_by_index(json_data, "fig", paper.paper_detail.key_fig)
        paper.valid = TaskStatus.TO_KEY_TAB_PROCESSING
        session.add(paper)  # 将修改后的对象标记为需要保存的对象
        session.flush()
    except Exception as e:
        arxiv_logger.error(f"Error processing paper id {arxiv_id} in process paper: {e}")
        paper.valid = ErrorCode.PARSE_RESULT_NOT_FOUND
        return f'Something wrong in processing Paper id {arxiv_id}'
    finally:
        return f'Paper id {arxiv_id} processed DONE'


@use_session()
def extract_key_tab(arxiv_id, session=None):
    try:
        paper = session.query(Papers).filter(Papers.external_id == arxiv_id).first()
        content_list_json_pth = os.path.join(os.path.join(daily_imgs_dir, f'{paper.id}_{paper.external_id}'),f'{paper.id}_{paper.external_id}_content_list.json')
        if not os.path.exists(content_list_json_pth):
            arxiv_logger.warning(f'{content_list_json_pth} does not exist. Skipping extract')
            paper.valid = ErrorCode.PDF_NOT_FOUND
            return f'PDF not found {arxiv_id}'
        with open(content_list_json_pth, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        if json_data is None:
            paper.valid = ErrorCode.PARSE_RESULT_NOT_FOUND
            return f'Something wrong in processing Paper id {arxiv_id}'

        fig_tab_dict = get_figs_tabs_LTS(json_data)
        paper.paper_detail.tab_caps = json.dumps(fig_tab_dict.get("tabs", []))
        paper.paper_detail.key_tab = judge_key_table(fig_tab_dict.get("tabs", []))
        paper.paper_detail.key_tab_name = get_img_path_by_index(json_data, "tab", paper.paper_detail.key_tab)
        paper.valid = TaskStatus.TO_CLUSTER
        session.add(paper)  # 将修改后的对象标记为需要保存的对象
        session.flush()
    except Exception as e:
        arxiv_logger.error(f"Error processing paper id {arxiv_id} in process paper: {e}")
        paper.valid = ErrorCode.PARSE_RESULT_NOT_FOUND
        return f'Something wrong in processing Paper id {arxiv_id}'
    finally:
        return f'Paper id {arxiv_id} processed DONE'

@use_session()
def generate_summary(paper_id,session=None):
    paper = session.query(Papers).filter(Papers.id == paper_id).first()

    try:
        key_idea =  get_key_idea(paper.paper_detail.abstract,default_model=medium_llm, temperature=0,lang='zh').IDEA
        print(key_idea)
        paper.paper_detail.key_idea = key_idea
        paper.valid = TaskStatus.TO_KEY_FIG_PROCESSING
        session.commit()
    except Exception as e:
        arxiv_logger.error(f"Error processing paper id {paper.external_id} in generate summary: {e}")
        paper.valid = ErrorCode.SUMMARY_ERROR
        session.commit()








@use_session()
def assign_short_urls_to_papers(session=None):
    papers = session.query(Papers).filter(
        Papers.valid == TaskStatus.TO_ANALYZE,
        func.date(Papers.download_date) == now.date()
    ).all()

    paper_ids = []

    for paper in papers:
        paper_ids.append(paper.external_id)

        shortUrl = get_short_url(paper.external_id.split('v')[0]).get('shortUrl')
        if shortUrl:
            paper.paper_detail.shortUrl = shortUrl
        else:
            paper.paper_detail.shortUrl = None
            paper.valid = ErrorCode.SHORT_URL_ERROR

        time.sleep(0.5)  # ✅ 仍保留节奏控制，避免 API 速率限制

    return paper_ids

def process_papers_concurrently(num_threads=12):#12
    paper_ids = assign_short_urls_to_papers()


    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(process_paper_lpqa, paper_id)
            for paper_id in paper_ids
        ]
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            arxiv_logger.info(result)
@use_session(commit=False)
def generate_summary_concurrently(num_threads=12,session=None):#12
    assign_short_urls_to_papers()
    papers = session.query(Papers).filter(
        Papers.valid == TaskStatus.TO_ANALYZE,
        func.date(Papers.download_date) == now.date()
    ).all()


    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(generate_summary, paper)
            for paper in papers
        ]
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            arxiv_logger.info(result)

@use_session()
def process_figs_concurrently(num_threads=12,session=None,):#12

    papers = session.query(Papers).filter(
        Papers.valid == TaskStatus.TO_KEY_FIG_PROCESSING,
        func.date(Papers.download_date) == now.date()
    ).all()


    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(extract_key_fig, paper.external_id)
            for paper in papers
        ]
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            arxiv_logger.info(result)

@use_session()
def process_tabs_concurrently(num_threads=12,session=None,):#12


    papers = session.query(Papers).filter(
        Papers.valid == TaskStatus.TO_KEY_TAB_PROCESSING,
        func.date(Papers.download_date) == now.date()
    ).all()



    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(extract_key_tab, paper.external_id)
            for paper in papers
        ]
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            arxiv_logger.info(result)


from sqlalchemy import func
from pathlib import Path
import re
from natsort import natsorted

def find_images(folder_path: Path, prefix: str):
    return natsorted(list(folder_path.glob(f"{prefix}-*.jpg")), key=lambda p: p.name)

from pathlib import Path
from sqlalchemy import func
from datetime import datetime
from natsort import natsorted

@use_session()
def fix_fig_tab_fields(session=None):

    def find_images(folder_path: Path, prefix: str):
        return natsorted(folder_path.glob(f"{prefix}-*.jpg"), key=lambda p: p.name)

    papers = session.query(Papers).filter(
        Papers.valid == TaskStatus.TO_CLUSTER,
        func.date(Papers.download_date) == now.date()
    ).all()

    for paper in papers:
        if paper.paper_detail.key_fig_name is not None and paper.paper_detail.key_tab_name is not None:
            continue
        else:
            if paper.paper_detail.key_fig < 0:
                tab_names = find_images(Path(daily_imgs_dir) / f"{paper.id}_{paper.external_id}", "tab")
                if len(tab_names) >= 2:
                    if paper.paper_detail.key_tab == 0:
                        paper.paper_detail.key_fig_name = tab_names[1].stem
                    else:
                        paper.paper_detail.key_fig_name = tab_names[0].stem
                else:
                    paper.valid = ErrorCode.INSUFFICIENT_IMGS
            elif paper.paper_detail.key_tab < 0:
                fig_names = find_images(Path(daily_imgs_dir) / f"{paper.id}_{paper.external_id}", "fig")
                if len(fig_names) >= 2:
                    if paper.paper_detail.key_fig == 0:
                        paper.paper_detail.key_tab_name = fig_names[1].stem
                    else:
                        paper.paper_detail.key_tab_name = fig_names[0].stem
                else:
                    paper.valid = ErrorCode.INSUFFICIENT_IMGS
            else:
                paper.valid = ErrorCode.INSUFFICIENT_IMGS
            session.flush()


if __name__ == '__main__':
    # process_papers_concurrently(num_threads=1)
    # arxiv_id = '2504.07955v1'
    # extract_key_fig(arxiv_id)
    # extract_key_tab(arxiv_id)
    assign_short_urls_to_papers()
    pass





