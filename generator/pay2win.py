import requests_cache
from reduct_db import PaperDAO

from crawler.bohrium_url import get_short_url
from db_services.render_service import RenderService
from operators.op_arxiv_downloader import ArxivDownloadJob
from operators.op_author_extractor import AuthorExtractorJob
from operators.op_fig_tab_processor import FigureTableJob
from operators.op_oachecker import OACheckerJob
from operators.op_render import RenderJob
from operators.op_script_generation import ScriptGenerateJob
from tools.markdown_tool import generate_final_csv, generate_markdown_from_csv

from tools.naip_tool import sum_citation_count_for_paper
from tools.ocr_tool import format_pdfs_onebyone_LTS
import validators
requests_cache.install_cache('demo_cache')
from cfg.STATUS import *
import langchain
langchain.debug = False
import arxiv
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from tqdm import tqdm
from cfg.safe_session import *

p2w_paper_arxiv_id = '2507.13332v1'

p2w_folder = os.path.join(arXiv_analysis_dir, p2w_paper_arxiv_id)

def init_args():
    # 创建ArgumentParser对象
    parser = argparse.ArgumentParser(description='Process some parameters.')
    # 添加'title'参数，这是一个必需的参数
    parser.add_argument('--low_cost_llm', type=str, default='moonshot-v1-8k')
    parser.add_argument('--long_context_llm', type=str, default='moonshot-v1-32k')
    parser.add_argument('--ultra_llm', type=str, default='gpt-4o')
    # 添加'pdf_path'参数，这是一个可选的参数
    parser.add_argument('--download_base_dir', type=str, default=r"I:\arxiv",
                        help='The optional path to a PDF file')
    parser.add_argument('--db_dir', type=str, default=r"I:\arxiv",
                        help='The optional path to a PDF file')
    parser.add_argument('--author_threshold', type=int, default=10000)
    parser.add_argument('--embedding', type=str, default=r"text-embedding-3-large")
    parser.add_argument('--GPT_enabled', action='store_true', default=True, help='Enable or disable GPT')

    # Adding the '--strategy' argument with restricted choices.
    parser.add_argument('--strategy', choices=['com', 'first_com', 'all'], default='first_com',
                        help='Choose a strategy among "com", "first_com", or "all"')
    # 解析命令行参数
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    session = session_factory()
    args = init_args()
    if not p2w_paper_arxiv_id.endswith('v1'):
        p2w_paper_arxiv_id += 'v1'

    csv_path = os.path.join(p2w_folder, 'reading.csv')
    os.makedirs(p2w_folder, exist_ok=True)


    print(f"What's your super power? \n Authors of {p2w_paper_arxiv_id}: Super Rich. ")

    print(f"Downloading Papers to {p2w_folder}. ")
    search_by_id = arxiv.Search(id_list=[p2w_paper_arxiv_id])
    client = arxiv.Client()
    arxiv_rst = []
    for result in tqdm(client.results(search_by_id)):
        arxiv_rst.append(result)

    adj = ArxivDownloadJob(download_folder=p2w_folder)
    pub_download_status = adj.download_single_paper(arxiv_rst[0])

    paper = PaperDAO(session=session).get_by_external_id(p2w_paper_arxiv_id)

    paper.whitelist_flag = WhitelistFlag.PROMOTED
    paper.valid = TaskStatus.TO_AUTHOR_INFO
    paper.paper_detail.shortUrl = get_short_url(p2w_paper_arxiv_id.replace('v1', '')).get('shortUrl')
    session.commit()

    format_pdfs_onebyone_LTS(input_dir=p2w_folder,output_dir=daily_imgs_dir, need_renmae=True)

    AuthorExtractorJob().process_single_author(p2w_paper_arxiv_id, pdf_pth=os.path.join(p2w_folder, f'{p2w_paper_arxiv_id}.pdf'))
    oa =''
    if OACheckerJob().check_oa_by_id(p2w_paper_arxiv_id, pdf_pth=os.path.join(p2w_folder, f'{p2w_paper_arxiv_id}.pdf')):
        if not validators.url(PaperDAO(session).get_by_external_id(p2w_paper_arxiv_id).paper_detail.code_url):
            print(f"Paper {p2w_paper_arxiv_id} is not OA. ")
            oa = input("Please provide a valid OA address. ")
        else:
            oa = PaperDAO(session).get_by_external_id(p2w_paper_arxiv_id).paper_detail.code_url
    else:
        print(f"Paper {p2w_paper_arxiv_id} is not OA. ")
        oa = input("Please provide a valid OA address. ")

    paper = PaperDAO(session=session).get_by_external_id(p2w_paper_arxiv_id)
    paper.paper_detail.code_url = oa
    session.commit()

    paper_id = PaperDAO(session).get_by_external_id(p2w_paper_arxiv_id).id
    ScriptGenerateJob().generate_summary_for_single_paper(paper_id)




    ftj = FigureTableJob()
    ftj.extract_fig(p2w_paper_arxiv_id)
    ftj.extract_tab(p2w_paper_arxiv_id)
    ftj.single_fix_figtab_missing(p2w_paper_arxiv_id)

    ScriptGenerateJob().generate_script_for_single_paper(p2w_paper_arxiv_id, pdf_pth=os.path.join(p2w_folder, f'{p2w_paper_arxiv_id}.pdf'))


    csv_path = os.path.join(p2w_folder, 'reading.csv')
    generate_final_csv(csv_path)
    generate_markdown_from_csv(csv_path, 1)

    rs = RenderService(session=session)
    rs.render_single_card(paper_id)


    # download_single_paper_LTS(arxiv_rst[0], p2w_folder)
    # is_oa = github_checker(os.path.join(p2w_folder,p2w_paper_arxiv_id+'.pdf'))
    # if not is_oa:
    #     print(f"Paper {p2w_paper_arxiv_id} is not OA. ")
    #     oa = input("Please provide a valid OA address. ")
    # print(f"Start analyzing authors...")
    # session = session_factory()
    # paper = session.query(Papers).filter(Papers.external_id == p2w_paper_arxiv_id).first()
    # paper.paper_detail.shortUrl = url
    # session.commit()
    # if paper:
    #     paper.TNCSI = -1
    #     paper.valid = TaskStatus.TO_AUTHOR_INFO
    #     session.commit()
    # else:
    #     raise FileNotFoundError
    # process_single_author(p2w_paper_arxiv_id, os.path.join(p2w_folder,p2w_paper_arxiv_id+'.pdf'),args)
    # print(f"Start analyzing content...")
    # process_paper_lpqa(p2w_paper_arxiv_id, p2w_folder, low_llm)
    # print(f"End analyzing as expected. Starting Card Generation.")
    #
    # if not is_oa:
    #     paper.paper_detail.oa = oa
    #     session.commit()
    # if paper:
    #     shortUrl = get_short_url(paper.external_id.split('v')[0]).get('shortUrl')
    #     author_cites = sum_citation_count_for_paper(paper.id,session)
    #     if paper.cn_script is None:
    #         reading_script_dict = generate_reading_script(paper)
    #         paper.paper_detail.cn_university = reading_script_dict['university']
    #         paper.paper_detail.cn_idea = reading_script_dict['idea']
    #         paper.paper_detail.cn_script = reading_script_dict['script']
    #         session.commit()
    #
    #     with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
    #         with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
    #             fieldnames = ['idLiterature', 'university', 'idea', 'script', 'author_cites', 'arxiv_id', 'title',
    #                           'abstract', 'oa_access', 'TNCSI','shortUrl']
    #             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #
    #             # 如果文件是空的，写入头部
    #             if csvfile.tell() == 0:
    #                 writer.writeheader()
    #             title = paper.title
    #             OA = oa_decode(paper.oa)
    #             arxiv_id = paper.external_id
    #             writer.writerow({
    #                 'idLiterature': paper.idLiterature,
    #                 'university': paper.cn_university,
    #                 'idea': paper.cn_idea,
    #                 'script': paper.cn_script,
    #                 'author_cites': author_cites,
    #                 'arxiv_id': arxiv_id,
    #                 'title': title,
    #                 'abstract': paper.paper_detail.abstract.strip().replace('\n', ' '),
    #                 'oa_access': OA,
    #                 'TNCSI': 0,
    #                 'shortUrl':shortUrl
    #             })
    #         # 读取CSV文件
    #         df = pd.read_csv(csv_path)
    #         df_unique = df.drop_duplicates(subset=['arxiv_id'], keep='first')
    #         df_unique.to_csv(csv_path, index=False, encoding='utf-8')
    #
    #
    #     try:
    #         html = generate_HTML_template_LTS(paper, p2w_folder)
    #
    #         html_template_file = os.path.join(p2w_folder, f'{paper.external_id}.html')
    #         if html is not None:
    #             write_string_to_file(html, html_template_file)
    #
    #             capture_div_screenshot(
    #                 html_template_file,
    #                 os.path.join(p2w_folder, f'{paper.external_id}.png')
    #             )
    #         paper.valid = ResultStatus.SUCCESS
    #         session.commit()
    #     except Exception as e:
    #         print(e)
    #         paper.valid = ErrorCode.GENERATE_ERROR
    #         session.commit()
    #
    #     generate_markdown_from_csv(os.path.join(p2w_folder, 'reading.csv'), 1)
    #     rename_images_by_citations(p2w_folder)
    # else:
    #     print('Paper not found')
