from sqlalchemy import exists

from cfg.langchain_imports import *
from cfg.safe_session import *
from cfg.STATUS import *

from concurrent.futures import as_completed


from analyzer.parser import author_parser
from crawler.gs_author_crawler import retrieve_author_citation_google
from reduct_db.db_entities import Papers, Authors, AuthorAffiliations, Affiliations, PaperAuthors
from database.DB_Util import current_day_data

from logs.loggers import arxiv_logger


import json

from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm



def author_info_extract(pth, default_model=low_llm, temperature=0, chunk_size=1000):
    loader = PDFMinerLoader(pth)

    def num_tokens_from_string(string: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(string))
        return num_tokens

    data = loader.load()
    raw_content = ''.join([d.page_content for d in data])
    # 使用 CharacterTextSplitter 分割文本

    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=chunk_size, chunk_overlap=0)
    raw_content = text_splitter.split_text(raw_content)[0]
    if arxiv_logger:
        arxiv_logger.info(f'Analyzing this paper cost {num_tokens_from_string(raw_content)} tokens')

    prompt_template = """
    Read the paper and identify the authors and the corresponding university or company of each author. 
    \nProvided paper: {context}\n
    Format Instructions:\n{format_instructions}
     """
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context"],
        partial_variables={"format_instructions": author_parser.get_format_instructions()},
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature, max_tokens=4096), prompt=PROMPT)
    rst = chain.run(context=raw_content)
    try:
        p_rst = author_parser.parse(rst)
    except OutputParserException as e:
        print(e)
        return None
    return p_rst.AUTHORS




def process_papers_authors_concurrently(num_threads=3):  # 3
    results = current_day_data(ID=TaskStatus.TO_AUTHOR_INFO)
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(process_single_author, paper.external_id)
            for paper in results
        ]
        for future in tqdm(as_completed(futures), total=len(futures)):
            future_result = future.result()


@use_session()
def process_single_author(arxiv_id, session=None):
    status = ""
    try:
        paper = session.query(Papers).filter(Papers.external_id == arxiv_id).first()

        if not paper:
            arxiv_logger.error(f'Error in processing paper {arxiv_id}: no paper found in the database')
            return False

        arxiv_logger.info(
            f'Retrieving authors info with {"GPT" if args.GPT_enabled else "BS4"} || Strategy employed: {args.strategy}.'
        )

        # 不再 remove session，这里继续使用当前 session 传下去
        process_lpqa_authors_LTS(paper.id, strategy=args.strategy, session=session)

        arxiv_logger.info(f'ALL PROCESS DONE for PAPER ID: {arxiv_id}')
        status = f'Paper id {arxiv_id} processed successfully.'

    except Exception as e:
        # 自动 rollback，无需再写 session.rollback()
        paper = session.query(Papers).filter(Papers.external_id == arxiv_id).first()
        if paper:
            paper.valid = ErrorCode.AUTHOR_INFO_ERROR
            # commit 会由装饰器统一处理
        arxiv_logger.error(f'Error processing paper id {arxiv_id}: {e}')
        status = f'Error processing paper id {arxiv_id}: {e}'

    return status


def get_aff_by_name(session, name):
    # 先查缓存
    for obj in session.new:
        if isinstance(obj, Affiliations) and obj.name == name:
            return obj
    # 再查数据库
    return session.query(Affiliations).filter(Affiliations.name == name).first()

def process_lpqa_authors_LTS(id, strategy='first_com',session=None):
    paper = session.query(Papers).filter(Papers.id == id).first()
    pdf_pth = os.path.join(arXiv_analysis_dir, paper.downloaded_pth)

    try:
        authors = author_info_extract(pdf_pth)
        if authors is None:
            raise OutputParserException

        # 保存原始作者信息
        paper.paper_detail.extract_author_raw_resp = json.dumps(authors)
        session.flush()

        # 决定哪些作者需要检索 GS
        if strategy == 'com':
            process_idx = [len(authors) - 1]
        elif strategy == 'first_com':
            process_idx = [0, len(authors) - 1]
        else:
            process_idx = list(range(len(authors)))  # 全部作者都检索

        author_cites = 0
        is_whitelisted_paper = False

        for a_i, author in enumerate(authors):
            # ---- Step 0: 解析作者信息 (name, aff) ----
            if len(author) != 2:
                print("Value Error in process_author: invalid author info.")
                continue
            extracted_name, extracted_aff = author

            # ---- Step 1: 解析机构层级，并拿到最底层 affiliation ----
            aff_parts = [aff.strip() for aff in extracted_aff.split(',')]
            parent_id = None
            for aff_part in aff_parts:
                aff_db = get_aff_by_name(session, aff_part)
                if not aff_db:
                    aff_db = Affiliations(name=aff_part, parent_aff=parent_id)
                    session.add(aff_db)
                session.commit()

                parent_id = aff_db.id
            smallest_aff = aff_db

            # ---- Step 2: 根据 (name, smallest_aff) 查询/创建作者 ----
            author_db = session.query(Authors).filter(
                Authors.name == extracted_name,
                exists().where(
                    (AuthorAffiliations.author_id == Authors.id) &
                    (AuthorAffiliations.affil_id == smallest_aff.id)
                )
            ).first()

            if not author_db:
                # 数据库里没有 => 创建
                new_author = Authors(name=extracted_name)
                session.add(new_author)
                session.flush()

                session.add(AuthorAffiliations(
                    author_id=new_author.id,
                    affil_id=smallest_aff.id
                ))
                session.flush()
                author_db = new_author
            else:
                # 如果已存在，就不新建，只保证其作者-机构关系已存在
                # （除非你想追加 start_date/end_date 等信息时再更新）
                pass

            paper_author_db = session.query(PaperAuthors).filter(PaperAuthors.author_id == author_db.id, PaperAuthors.paper_id == paper.id).first()
            if paper_author_db is None:
                session.add(PaperAuthors(author_id=author_db.id, paper_id=paper.id, author_order=a_i, affil_id=smallest_aff.id))
                session.flush()
            # ---- Step 3: 只有在 process_idx 内的作者才检索 Google Scholar ----
            if a_i in process_idx:
                # 清理掉 * 符号等
                extracted_name_clean = extracted_name.replace('*', '')
                extracted_aff_clean = extracted_aff.replace('*', '')

                info = retrieve_author_citation_google(extracted_name_clean, extracted_aff_clean)

                # 检查是否在白名单
                if is_whitelisted(extracted_name_clean, extracted_aff_clean):
                    is_whitelisted_paper = True

                if info:
                    # 如果拿到了正确的 GS 信息
                    cite = info.get('cited_by_count', 0) or 0
                    gs_id = info.get('user_id')  # 可能为空
                    author_cites += cite  # paper 的引用数累加
                    author_with_gsid = session.query(Authors).filter(Authors.gs_id == gs_id).first()
                    if not author_with_gsid: # 如果没有指定gs id的作者
                        # 更新此作者的引用次数
                        author_db.cites = cite

                        # 若此作者还没有 gs_id，就写入；否则不覆盖
                        if gs_id and not author_db.gs_id:
                            author_db.gs_id = gs_id

                        session.flush()
                    else:
                        author_db.cites = cite
                        session.flush()
                else:
                    # GS 未检索到或匹配失败 => 什么都不做
                    pass
            else:
                # 不在 process_idx => 不检索 GS，也不更新 cites
                pass
        session.flush()

        # ---- Step 4: 更新论文的所有作者引用总和 ----
        paper = session.query(Papers).filter(Papers.id == paper.id).first()
        paper.paper_detail.author_cites_w_strategy = author_cites
        if is_whitelisted_paper:
            paper.TNCSI = 1
            paper.whitelisted = WhitelistFlag.AUTHOR

        paper.valid = TaskStatus.TO_OA_CHECK

        session.flush()
        return True

    except Exception as e:
        arxiv_logger.error(f'Error processing paper id {paper.external_id}: {e}')
        raise e


def is_whitelisted(name, institution=None, mode=3):
    """
    确认指定的姓名和机构是否在白名单中。

    参数：
        name (str): 姓名，必选。
        institution (str, optional): 机构，可选。
        mode (int): 模式，1 表示严格匹配，2 表示忽略机构，3 表示依据 JSON 决定。

    返回：
        bool: 如果匹配白名单则返回 True，否则返回 False。
    """
    try:
        # 加载白名单数据
        with open(r"C:\Users\Ocean\Documents\GitHub\Arxiv_Reduct\analyzer\whitelist.json", "r", encoding="utf-8") as file:
            whitelist = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # 如果白名单文件不存在或格式错误，返回 False
        return False
    name = name.lower().strip()
    if institution is None:
        institution = ""
    institution = institution.lower().strip()
    # 遍历白名单进行匹配
    for entry in whitelist:
        if not isinstance(entry, dict):
            continue  # 确保白名单条目是字典

        entry_name = entry.get("name").lower().strip()
        entry_institution = entry.get("institution").lower().strip()
        strict = entry.get("strict", False)  # 默认不严格匹配

        if mode == 1 or (mode == 3 and strict):  # 严格匹配
            if name == entry_name and institution == entry_institution:
                return True
        elif mode == 2 or (mode == 3 and not strict):  # 忽略机构
            if name == entry_name:
                return True

    return False


if __name__ == "__main__":
    # process_single_author('2408.03934v1')

    print(is_whitelisted("Kaiming He", "HK"))