import argparse
import csv
import datetime
import re
import time
import cv2
import pandas as pd
import tiktoken
from PIL import Image
from langchain.chains.llm import LLMChain
from langchain_community.chat_models import ChatOpenAI
from langchain_community.document_loaders import PDFMinerLoader
from langchain_core.exceptions import OutputParserException
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from retry import retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import fitz
import torch
import langchain
langchain.debug = False
import numpy as np
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import os, json
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List,  OrderedDict
import langchain
langchain.debug = False
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from doclayout_yolo import YOLOv10
import uuid
import os
import shutil

# 全局定义 YOLO 模型变量，避免后续报错
_model = None
class GPT_Paper_Response(BaseModel):
    # AUTHORS: List[List[str]] = Field(
    #     description="Author name and the corresponding affiliation's full name. Please provide the official name of the institution only, excluding any labs, departments, country or regional names, as well as any abbreviations or postal codes. Format the answer like [[Name, Affiliation], [Name, Affiliation],...], e.g. [['Yann LeCun', 'New York University'], ...]. Add an asterisk (*) after the name of the communicating author if you can confirm it.")
    FIGURE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all figures in the order they actually appear in the document. If the caption is too long, you can keep only the first sentence of the caption for each image. Format your answer like ['Fig. 1: CAPTION', 'Fig. 2: CAPTION', ...].")
    TABLE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all tables in the order they actually appear in the document. If the caption is too long, you can keep only the first sentence of the caption for each table. Format your answer like ['Tab. 1: CAPTION', 'Tab. 2: CAPTION', ...]. ")
    IDEA: str = Field(
        description="A concise summary of the core method proposed in this paper. To answer this question, you MUST NOT refer to the abstract and the conclusion section")
    OA: List[str] = Field(
        description="Links to the proposed open-source code or datasets of the given paper? Links mentioned in the reference list can not be the answer. Format the answer like ['https://xxx', ...]. If no proposed open-source code or datasets are reported, output as []")
class Fig_Tab_Response(BaseModel):
    FIGURE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all figures in the order they actually appear in the document. Format your answer like ['Fig. 1: CAPTION', 'Fig. 2: CAPTION', ...].")
    TABLE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all tables in the order they actually appear in the document.  Format your answer like ['Tab. 1: CAPTION', 'Tab. 2: CAPTION', ...]. ")

class Idea_Response(BaseModel):
    IDEA: str = Field(description="A concise summary of the core method proposed in this paper. ")
class OA_Response(BaseModel):
    OA: List[str] = Field(
        description="Links to the proposed open-source code or datasets of the given paper? Links mentioned in the reference list can not be the answer. Format the answer like ['https://xxx', ...]. If no proposed open-source code or datasets are reported, output as []")



class Paper_Info_Entity():
    FIGURE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all figures in the order they actually appear in the document. e.g. ['Fig. 1: The network architecture framework', 'Fig. 2: Visualization results', ...]")
    TABLE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all tables in the order they actually appear in the document. e.g. ['Tab. 1: Comparision with SOTA methods', 'Tab. 2: Abalation Study', ...]")
    IDEA: str = Field(description="A concise summary of the core method proposed in this paper.")

class Paper_Info_Response(BaseModel):
    FIGURE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all figures in the order they actually appear in the document. If the caption is too long, you can keep only the first sentence of the caption for each image. Format your answer like ['Fig. 1: CAPTION', 'Fig. 2: CAPTION', ...].")
    TABLE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all tables in the order they actually appear in the document. If the caption is too long, you can keep only the first sentence of the caption for each table. Format your answer like ['Tab. 1: CAPTION', 'Tab. 2: CAPTION', ...]. ")
    IDEA: str = Field(
        description="A concise summary of the core method proposed in this paper. To answer this question, you MUST NOT refer to the abstract and the conclusion section")
class Author_Response(BaseModel):
    AUTHORS: List[List[str]] = Field(
        description="Provide the official name of each author and their corresponding institution in the following "
                    "format: [[Name, Affiliation], [Name, Affiliation], ...]. Use the full, official name of the "
                    "institution only, excluding any sub-affiliations (e.g., DARPA Labs, Tencent Labs), departments ("
                    "e.g., College of Computer Science), countries, regions, abbreviations, or postal codes. Format your answer like"
                    "[['Yann LeCun', 'New York University'], [Sam Altman, OpenAI] ...].")


lpqa_parser = PydanticOutputParser(pydantic_object=GPT_Paper_Response)
fig_tab_parser = PydanticOutputParser(pydantic_object=Fig_Tab_Response)
idea_parser = PydanticOutputParser(pydantic_object=Idea_Response)
oa_parser = PydanticOutputParser(pydantic_object=OA_Response)
paper_info_parser = PydanticOutputParser(pydantic_object=Paper_Info_Response)
author_parser = PydanticOutputParser(pydantic_object=Author_Response)
# 配置区域
def init_args():

    parser = argparse.ArgumentParser(description='Process some parameters.')
    parser.add_argument('--ori_pdf_pth', type=str, default='')
    parser.add_argument('--low_cost_llm', type=str, default='gpt-4o-mini')
    parser.add_argument('--medium_llm', type=str, default='gpt-4o')
    parser.add_argument('--ultra_llm', type=str, default='gpt-4o')
    # 添加'pdf_path'参数，这是一个可选的参数
    parser.add_argument('--download_base_dir', type=str, default=r"I:\arxiv",help='The optional path to a PDF file')
    parser.add_argument('--detect_model_path', type=str, default=r'K:\weights\doclayout_yolo_doclaynet_imgsz1120_docsynth_pretrain.pt', help='The optional path to a PDF file')
    # 解析命令行参数
    args = parser.parse_args()
    return args
root_html_dir = os.path.join(os.path.dirname(__file__), 'generator', 'html_template')
args = init_args()
paper_id = str(uuid.uuid4())

pdf_path = args.ori_pdf_pth

# 获取目录和新的路径
pdf_dir = os.path.dirname(pdf_path)
new_pdf_path = os.path.join(pdf_dir, f"{paper_id}.pdf")

# 重命名（或复制并重命名）
shutil.move(pdf_path, new_pdf_path)  # 或者用 os.rename(pdf_path, new_pdf_path)
pdf_path = new_pdf_path


base_analysis_dir = os.path.join(args.download_base_dir, paper_id)
low_llm = args.low_cost_llm
medium_llm = args.medium_llm
ultra_llm = args.ultra_llm

os.makedirs(base_analysis_dir, exist_ok=True)
csv_path = os.path.join(base_analysis_dir, 'reading.csv')


detect_model_path = args.detect_model_path
detect_imgs_dir = os.path.join(base_analysis_dir, 'imgs')

# 代码区 （一般情况无需修改）

def single_det_yolo_batch(images, imgsz=1024, conf=0.5):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    global _model
    if _model is None:
        print("Loading YOLO model...")
        _model = YOLOv10(detect_model_path)  # lazy load
        print(f"Using device: {device}")
    else:
        print("YOLO model already loaded.")
    # 只需 BGR -> RGB，原图尺寸直接进模型，不做 resize
    rgb_imgs = [cv2.cvtColor(img, cv2.COLOR_BGR2RGB) for img in images]

    # 直接送入模型，模型自己处理尺寸/letterbox
    det_results = _model.predict(
        rgb_imgs,
        imgsz=imgsz,     # 模型内部 letterbox 或动态缩放
        conf=conf,
        device=device,
        iou=0.1
    )

    return det_results

def filter_list(input_list, regex=None):
    if regex is None:
        pattern = re.compile(r'www\.|http:|https:|\.com|github|sway')
    else:
        pattern = re.compile(regex)
    output_set = set()
    output_list = []

    for item in input_list:
        # 使用预编译的正则表达式一次性检查所有子串
        if pattern.search(item.page_content):
            # 只添加不在集合中的项
            if item.page_content not in output_set:
                output_list.append(item)
                output_set.add(item.page_content)

    return output_list

def parse_abstract_for_oa(title, abstract):
    """
    利用 LLMChain 对摘要进行解析，返回解析结果 naive_parse_resp。
    如果解析器报错或摘要为空，则返回 None。
    """
    if not abstract or len(abstract) == 0:
        return None

    # 以下 prompt 与原代码完全一致
    prompt_template = """
                Below are abstract from a certain academic paper extracted from an academic paper PDF file. Please parse the content and use it to answer the user question. 

                Title: {title}
                Abstract: {abs}

                Question: Based on the provided sentences, extract the link of the URL of the current paper's repository. 

                Do not attempt to fabricate an answer.

                Format Instruction:
                {format_instructions}
                """
    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["title", 'abs'],
        partial_variables={"format_instructions": oa_parser.get_format_instructions()},
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=low_llm, temperature=0), prompt=PROMPT)

    # 调用 LLMChain
    only_abs_rst = chain.run(title=title, abs=abstract)

    # 解析返回值
    try:
        naive_parse_resp = oa_parser.parse(only_abs_rst)
        return naive_parse_resp
    except OutputParserException as e:
        print(f'OA Checker Parser Error in abs: {e}. || {only_abs_rst}. Continue to Ensemble Check')
        return None

def chunk_pdf(pdf_pth,chunk_size=800,overlap=0,separators= [',', "\n\n", ' ']):
    try:
        loader = PDFMinerLoader(pdf_pth)
        data = loader.load()
        raw_content = ''.join([d.page_content for d in data])
        text_splitter = RecursiveCharacterTextSplitter(
            # Set a really small chunk size, just to show.
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=separators
        )
    # text_splitter = SemanticChunker(OpenAIEmbeddings())
        texts = text_splitter.create_documents([raw_content])
        return texts
    except Exception as e:
        return None

def naive_figtab_checker(pdf_pth):
    try:
        loader = PDFMinerLoader(pdf_pth)
        data = loader.load()
        raw_content = ''.join([d.page_content for d in data])
        text_splitter = RecursiveCharacterTextSplitter(
            # Set a really small chunk size, just to show.
            chunk_size=400,
            chunk_overlap=0,
            separators=[',', '.',"\n\n", ' ']
        )
        # text_splitter = SemanticChunker(OpenAIEmbeddings())
        texts = text_splitter.create_documents([raw_content])
    except Exception as e:
        return []
    rst = {'fig': filter_list(texts, r'\b(Fig\.?|Figure|FIG|FIGURE)\b'), 'tab': filter_list(texts, r'\b(Table|TAB|TABLE|Tab\.)\b')}
    return rst

def chunk_pdf_for_oa(pdf_pth, arxiv_id):
    """
    对 PDF 做大块、小块分割。返回 (major_intro_chunk, top_ss_chunks, pdf_corrupted)
    如果 PDF 无法分块则标记 pdf_corrupted = True
    """
    major_intro_chunk = chunk_pdf(pdf_pth, chunk_size=2000)
    top_ss_chunks = chunk_pdf(pdf_pth, chunk_size=400)

    if major_intro_chunk is None or top_ss_chunks is None:
        return None, None, True

    # 取第一个大块
    major_intro_chunk = major_intro_chunk[0]
    top_ss_chunks = filter_list(top_ss_chunks)
    top_ss_chunks = [i.page_content for i in top_ss_chunks]

    return major_intro_chunk, top_ss_chunks, False

def parse_pdf_text_for_oa(major_intro_chunk, top_ss_chunks):
    if not top_ss_chunks or len(top_ss_chunks) == 0:
        return None, None, True
    prompt_template = """
                Check if the authors have mentioned sharing their code, dataset, or something related on the website? Pay attnetion to sentences like 'Code is released at xxx', 'Project page is xxx', etc. If so, please list these links.
                Text Chunks might contain URLs: {intro_chunk}

                Do not attempt to fabricate an answer.

                Format Instruction:
                {format_instructions}
                """
    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=['intro_chunk'],
        partial_variables={"format_instructions": oa_parser.get_format_instructions()},
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=low_llm, temperature=0), prompt=PROMPT)

    intro_rst = chain.run(intro_chunk=major_intro_chunk)

    try:
        intro_parse_resp = oa_parser.parse(intro_rst)
        naive_parse_resp = intro_parse_resp  # 此处暂返回相同结果
        return naive_parse_resp, intro_parse_resp, False
    except OutputParserException as e:
        print(f'OA Checker Parser Error: {e}. || {top_ss_chunks} ')
        return None, None, True

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser, OutputParserException
from pydantic import BaseModel, Field

# 1. 定义结构化输出模型
class TitleAbstractResponse(BaseModel):
    TITLE: str = Field(description="The title of the paper.")
    ABSTRACT: str = Field(description="The abstract of the paper.")

ta_parser = PydanticOutputParser(pydantic_object=TitleAbstractResponse)

# 2. 构建 Chain
def build_title_abs_chain(model_name="gpt-3.5-turbo", temperature=0):
    prompt_template = """
    Please extract the **title** and the **abstract** of the paper from the following content.
    The abstract should be as complete and faithful as possible. Output in JSON format.

    Paper content:
    {context}

    Format Instructions:
    {format_instructions}
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context"],
        partial_variables={"format_instructions": ta_parser.get_format_instructions()}
    )

    return LLMChain(
        llm=ChatOpenAI(model_name=model_name, temperature=temperature),
        prompt=prompt
    )

# 3. 主函数（只用第一个 chunk）
def get_title_abs_from_pdf(pdf_pth, model_name="gpt-3.5-turbo"):

    chunks = chunk_pdf(pdf_pth, chunk_size=2000)
    if not chunks:
        raise ValueError("PDF parsing failed or returned empty content.")

    first_chunk = chunks[0].page_content
    chain = build_title_abs_chain(model_name=model_name)

    raw_output = chain.run(context=first_chunk)

    try:
        parsed = ta_parser.parse(raw_output)
    except OutputParserException:
        print(f"Parse failed. Raw output:\n{raw_output}")
        fixer = OutputFixingParser.from_llm(parser=ta_parser, llm=ChatOpenAI(model_name=model_name))
        parsed = fixer.parse(raw_output)
        print(f"Fixed output:\n{parsed}")

    return parsed

def get_figs_tabs(pth, default_model="gpt4o-mini", temperature=0):
    try:
        top_ss_chunks = naive_figtab_checker(pth)
        figs = top_ss_chunks['fig']
        tabs = top_ss_chunks['tab']
        top_fig_chunks = [i.page_content for i in figs]
        top_tab_chunks = [i.page_content for i in tabs]
        if len(top_ss_chunks) > 0:
            prompt_template = """Below are sentences extracted from an academic paper PDF file that contain mentions of figures and tables. Please parse the content and use it to extract all the figure or table captions present in the paper. Focus specifically on any text chunks containing the terms 'fig', 'figure', or 'table', 'tab'.

            Text Chunks (Figure): {fig_chunks}
            Text Chunks (Table): {tab_chunks}
            Question: Based on the provided sentences, extract all figure or table captions from the text. Ensure only the captions belonging to figures, charts, or tables from the current paper are included.

            Format Instruction:
            {format_instructions}
            """

            PROMPT = PromptTemplate(
                template=prompt_template, input_variables=['fig_chunks','tab_chunks'],
                partial_variables={"format_instructions": fig_tab_parser.get_format_instructions()},
            )
            chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature),
                             prompt=PROMPT)

            rst = chain.run(fig_chunks=' || '.join(top_fig_chunks),tab_chunks=' || '.join(top_tab_chunks))

            try:
                p_rst = fig_tab_parser.parse(rst)
            except OutputParserException as e:
                print(f'OA Checker Parser Error: {e}. || {top_ss_chunks} || {rst}')
                return False
            if len(p_rst.FIGURE_CAPTION + p_rst.TABLE_CAPTION) > 0:
                return p_rst
            else:
                return None
        else:
            return None
    except Exception as e:

        raise Exception('Error occurs in github_checker:', e)
        return None

def get_key_idea(abstract,default_model=medium_llm, temperature=0,lang='en'):
    if lang == 'en':
        prompt_template = """
            I need a concise summary of the core method proposed in this paper. Could you distill the provided abstract of paper into a single, clear sentence?
            \nProvided paper abstract: {context}\n
            Format Instructions:\n{format_instructions}
             """
    elif lang == 'zh':
        prompt_template = """
            请用**中文**，并且**仅用一句话**简洁总结本文的核心方法。
            确保总结内容简短、准确，不要有任何冗余或不必要的细节。请考虑使用本文提出、我们提出等方式开头。
            \n论文摘要：{context}\n
            格式要求：{format_instructions}"""
    else:
        prompt_template = """
                    I need a concise summary of the core method proposed in this paper. Could you distill the provided abstract of paper into a single, clear sentence?
                    \nProvided paper abstract: {context}\n
                    Format Instructions:\n{format_instructions}
                     """
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context"],
        partial_variables={"format_instructions": idea_parser.get_format_instructions()},
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)

    rst = chain.run(context=abstract)

    try:
        p_rst = idea_parser.parse(rst)
    except OutputParserException as e:
        print(f'raw output {rst}')
        fix_parser = OutputFixingParser.from_llm(parser=idea_parser, llm=ChatOpenAI(model_name=medium_llm, temperature=0))

        p_rst = fix_parser.parse(rst)

        print(f'fixed output {p_rst}')
    return p_rst

def single_paper_info_extract(abstract, pdf_pth,default_model=low_llm, temperature=0):


    idea_rst = get_key_idea(abstract, default_model=default_model, temperature=temperature,lang='zh')
    fig_tab_rst = get_figs_tabs(pth=pdf_pth, default_model=default_model, temperature=temperature)

    single_paper_info_entity =  Paper_Info_Entity()
    single_paper_info_entity.FIGURE_CAPTION = fig_tab_rst.FIGURE_CAPTION
    single_paper_info_entity.TABLE_CAPTION = fig_tab_rst.TABLE_CAPTION
    single_paper_info_entity.IDEA = idea_rst.IDEA

    return single_paper_info_entity

def get_html_code(html_file_path, variables):
    import datetime
    """
    Generates a dynamic HTML file by replacing placeholders in a template.

    Args:
        html_file_path (str): Path to the HTML template file.
        variables (dict): Dictionary of variables to replace placeholders in the template.

    Returns:
        None
    """
    # Read the HTML template from the file
    with open(html_file_path, "r", encoding="utf-8") as template_file:
        html_template = template_file.read()

    # Fill the template with data
    html_content = html_template.format(**variables)
    return html_content

def judge_key_figure(gpt_response, default_model=low_llm, temperature=0):
    fig_caps = gpt_response.FIGURE_CAPTION
    prompt_template = """
    Below are all the figure captions from an article, and you need to determine which one is the main figure based on these captions. The main figure typically refers to a flowchart of methods, framework diagram, model structure chart, etc. Since I will use your response directly in subsequent programs, your reply must contain only one number, which is the sequence number of the picture.
    \n\n{caps}
     """
    caps = '; '.join(fig_caps)

    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["caps"]
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)
    rst = chain.run(caps=caps)
    try:
        rst = int(rst)
    except:
        return 1
    return rst

def judge_key_table(gpt_response, default_model=low_llm, temperature=0):
    tab_caps = gpt_response.TABLE_CAPTION
    prompt_template = """
    Below are all the table captions from an article, and you need to determine which one is the most important table based on these captions. Typically, this would be a table comparing the proposed method with other approaches to show its superiority. Since I will use your response directly in subsequent programs, your reply must contain only one number, which is the sequence number of the table.
    \n\n{caps}
     """
    caps = '; '.join(tab_caps )
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["caps"]
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)
    rst = chain.run(caps=caps)
    try:
        rst = int(rst)
    except:
        return 1
    return rst

def process_paper(pdf_pth,low_llm: str):
    ta = get_title_abs_from_pdf(pdf_pth)
    title = ta.TITLE
    abstract = ta.ABSTRACT
    if not os.path.exists(pdf_pth):
        return {
            "status": "PDF_NOT_FOUND",
            "message": f"PDF not found at {pdf_pth}"
        }


    lpqa = single_paper_info_extract(
        abstract=abstract,
        pdf_pth=pdf_pth,
        default_model=low_llm
    )

    raw_resp = json.dumps(lpqa.__dict__, indent=0)

    result = {
        "status": "SUCCESS",
        "title": title,
        "abstract": abstract,
        "key_idea": lpqa.IDEA,
        "fig_caps": lpqa.FIGURE_CAPTION,
        "tab_caps": lpqa.TABLE_CAPTION,
        "key_fig": judge_key_figure(lpqa),
        "key_tab": judge_key_table(lpqa),
        "raw_resp": raw_resp,
    }

    return result

def write_string_to_file(content, file_path):
    # 使用 "w" 模式打开文件，表示写入（如果文件已存在，则会被覆盖）
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def capture_div_screenshot(absolute_path, output_pth, capture_class='card-wrapper', scale_factor=1):
    # output_filename = output_filename.split('.')[0]
    # 构造本地文件 URL
    url = f"file:///{absolute_path.replace(os.path.sep, '/')}"
    # 配置 Chrome 选项（无头模式）
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # 新无头模式
    chrome_options.add_argument("--window-size=1600,2500")  # 设置初始窗口
    chrome_options.add_argument("--force-device-scale-factor=1")  # 禁止缩放干扰
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--hide-scrollbars")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    # 等待页面加载
    time.sleep(1)
    # 找到目标元素截图（原始分辨率）
    element = driver.find_element(By.CLASS_NAME, capture_class)
      # 临时文件保存原始图
    element.screenshot(output_pth)
    driver.quit()
    if scale_factor != 1:
        # 用 Pillow 打开原始图，进行缩放处理
        with Image.open(output_pth) as im:
            orig_w, orig_h = im.size
            new_size = (int(orig_w * scale_factor), int(orig_h * scale_factor))
            # 使用高质量缩放算法：LANCZOS
            im_scaled = im.resize(new_size, resample=Image.LANCZOS)
            output_pth = output_pth.replace('.png', '.jpg')
            # 保存到最终路径（可设置为 JPEG 或 PNG）
            im_scaled.save(output_pth, dpi=(300, 300))
        # # 删除临时原始图
        # os.remove(tmp_path)
    print(f"[√] Saved scaled image to {output_pth}")

def convert_pdf_to_image(pdf_path, rst_mode='bgr',output_path=None,dpi=300):
    '''
    返回BGR图像
    :param pdf_path:
    :param output_path:
    :return:
    '''

    doc = fitz.open(pdf_path)
    imgs = []

    for i in range(len(doc)):
        page = doc.load_page(i)  # 加载页面
        pix = page.get_pixmap(dpi=dpi)  # 创建高分辨率的pixmap
        # 将Pixmap对象的图像数据转换为numpy数组
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if rst_mode == 'bgr':
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        imgs.append(img)
        if output_path:
            output_file = os.path.join(output_path, f"output_{i}.jpeg")
            cv2.imwrite(output_file, img)
    return imgs

def get_figs_tabs_yolo_batch(pdf_path, output_dir: str = None, show_rst=False, batch_size=4, imgsz=1024, conf=0.5):
    from tqdm import tqdm  # 可选：显示进度条
    # get screenshots of PDF file
    pdf_imgs = convert_pdf_to_image(pdf_path)

    # Mapping of target classes
    target_names = {'Picture': 6, 'Table': 8}

    figs, tabs = [], []
    figs_names, tabs_names = [], []

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # Process in batches
    for i in tqdm(range(0, len(pdf_imgs), batch_size)):
        batch_imgs = pdf_imgs[i:i + batch_size]
        batch_indices = list(range(i, i + len(batch_imgs)))  # 当前批次的页码

        # Run YOLO batch detection
        det_results = single_det_yolo_batch(batch_imgs, imgsz=imgsz, conf=conf)

        for img_idx, (img, det) in enumerate(zip(batch_imgs, det_results)):
            page_idx = batch_indices[img_idx]

            # 提取目标框
            picture_boxes = [box.xyxy.squeeze().cpu().numpy().astype(int)
                             for box in det.boxes if int(box.cls) == target_names['Picture']]
            table_boxes = [box.xyxy.squeeze().cpu().numpy().astype(int)
                           for box in det.boxes if int(box.cls) == target_names['Table']]

            # 提取并保存图片
            for j, box in enumerate(picture_boxes):
                x1, y1, x2, y2 = box
                cropped_img = img[y1:y2, x1:x2]
                figs.append(cropped_img)
                name = f"fig-{page_idx}-{j}"
                figs_names.append(name)
                if output_dir:
                    cv2.imwrite(os.path.join(output_dir, f"{name}.png"), cropped_img)

            for j, box in enumerate(table_boxes):
                x1, y1, x2, y2 = box
                cropped_img = img[y1:y2, x1:x2]
                tabs.append(cropped_img)
                name = f"tab-{page_idx}-{j}"
                tabs_names.append(name)
                if output_dir:
                    cv2.imwrite(os.path.join(output_dir, f"{name}.png"), cropped_img)

    return {
        'figs': figs,
        'tabs': tabs,
        'pages': pdf_imgs,
        'figs_names': figs_names,
        'tabs_names': tabs_names
    }

def generate_HTML_template(title, authors, demo_addr,  key_idea, key_tab, key_fig,publication_date, venue,  base_analysis_dir =base_analysis_dir):
    authors_title = ''
    os.makedirs(os.path.join(detect_imgs_dir , f'{paper_id}'), exist_ok=True)
    fig_tab = get_figs_tabs_yolo_batch(
        os.path.join(base_analysis_dir, paper_id + '.pdf'),  # + f'\\{paper_db.ori_index}_{paper_db.external_id}'
        output_dir=str(os.path.join(detect_imgs_dir , paper_id)),
        show_rst=False,
        batch_size=16,
        imgsz=1024,
        conf=0.5
    )
    figs = fig_tab['figs']
    tabs = fig_tab['tabs']

    num_detected_figs = len(figs)
    num_detected_tabs = len(tabs)

    ultimate_fig_idx = -1
    ultimate_tab_idx = -1

    key_fig_pth = os.path.join(base_analysis_dir, f'{paper_id}-fig.png')
    key_tab_pth = os.path.join(base_analysis_dir, f'{paper_id}-tab.png')

    try:
        key_fig_index = int(key_fig)
        key_fig = figs[key_fig_index - 1]
        cv2.imwrite(key_fig_pth, key_fig)
        fig_html = f'<img src = "{os.path.basename(key_fig_pth)}" />'
        ultimate_fig_idx = key_fig_index - 1
    except IndexError:
        print(
            f'IndexError: key_fig has only {len(figs)} elements, but an index of {key_fig} is called. Using the first Figure instead.')
        if len(figs) > 0:
            key_fig = figs[0]
            cv2.imwrite(key_fig_pth, key_fig)
            fig_html = f'<img src = "{os.path.basename(key_fig_pth)}" />'
            ultimate_fig_idx = 0

        else:
            fig_html = ''

    try:
        key_tab_index = int(key_tab)
        key_tab = tabs[key_tab_index - 1]
        cv2.imwrite(key_tab_pth, key_tab)
        tab_html = f'<img src = "{os.path.basename(key_tab_pth)}" />'
        ultimate_tab_idx = key_tab_index - 1
    except IndexError:
        print(
            f'IndexError: key_tab has only {len(tabs)} elements, but an index of {key_tab} is called. Using the first Table instead.')
        if len(tabs) > 0:
            key_tab = tabs[0]
            cv2.imwrite(key_tab_pth, key_tab)
            tab_html = f'<img src = "{os.path.basename(key_tab_pth)}" />'
            ultimate_tab_idx = 0

        else:
            tab_html = ''

    if fig_html == '':  # 图片为0 去tab找
        if num_detected_tabs >= 2:
            key_fig = tabs[1] if ultimate_tab_idx == 0 else tabs[0]
            cv2.imwrite(key_fig_pth, key_fig)
            fig_html = f'<img src = "{os.path.basename(key_fig_pth)}" />'

    if tab_html == '':  # tab 为0 去fig找
        if num_detected_figs >= 2:
            key_tab = figs[1] if ultimate_fig_idx == 0 else figs[0]
            cv2.imwrite(key_tab_pth, key_tab)
            tab_html = f'<img src = "{os.path.basename(key_tab_pth)}" />'

    if tab_html == '' or fig_html == '':
        print(f'Still found no images for generation for {paper_id}. SKIPING NOW.')
        return None
    pub_date = publication_date.strftime('%Y-%m-%d')

    variables_pack = {
        'title': title,
        'authors': authors,
        'OA': demo_addr,
        'authors_title': authors_title,
        'key_idea': key_idea,
        'fig_html': fig_html,
        'tab_html': tab_html,
        'pub_date': pub_date,
        'arxiv_id': venue,
        'css_pth': os.path.join(root_html_dir, f'paper_card.css'),
        'js_pth': os.path.join(root_html_dir, f'paper_card.js'),
    }

    return get_html_code(r'C:\Users\Ocean\Documents\GitHub\Arxiv_Reduct\generator\html_template\paper_card.html',variables_pack)

@retry(delay=6, tries=10)
def generate_reading_script(raw_resp, authors):
    rst = {}
    universities = []  # [author[1].replace('*', '') for author in raw_resp.get("AUTHORS")]
    for author in authors:
        if len(author) == 2:
            universities.append(author[1].replace('*', ''))

    # 去重并保持顺序
    unique_universities = list(OrderedDict.fromkeys(universities))
    # 判断机构数量
    if len(unique_universities) > 3:
        unique_universities = unique_universities[:2] + [unique_universities[-1]]
    unique_universities_str = ", ".join(unique_universities)

    university_template = """Given the provided address or affiliation information, identify and extract only the names of the primary institutions such as universities, companies, or main research bodies. Translate these names into Chinese, ensuring accuracy and EXCLUDING any sub-institutions, departments, or specific research centers. Output the translated names in the format: Organization 1, Organization 2, Organization 3. Include only the requested information without any additional content. {universities}"""
    PROMPT = PromptTemplate(
        template=university_template, input_variables=["universities"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=low_llm, temperature=0), prompt=PROMPT)
    uni_gpt_resp = chain.run(universities=str(unique_universities_str))
    rst['university'] = uni_gpt_resp

    ENG_script_prompt = '''Please draft a brief script for sharing an academic paper based on the information provided below. The language style should be clear, professional, and natural, tailored to the target audience (graduate students, professors). The content should be written in the third person.

Details are as follows:
Author Organization: {org} 
Core Idea of the Paper: {idea}

Begin the script with the sentence structure “The [organization name] proposed/introduced/presented the xx method,” replacing “[organization name]” with the organization provided. Notes:
(1) You must replace “[organization name]” with the provided organization name (remove duplicated if necessary);
(2) Do not fabricate any information not explicitly provided;
(3) Describe the method solely based on the provided core idea. Do not use evaluative or summarizing language such as “offers new insights” or “provides important resources.” Do not include any commentary, conclusions, or summaries;
(4) The output must only contain the draft script based on the core idea, with no additional descriptions or explanations.
'''
    PROMPT = PromptTemplate(
        template=ENG_script_prompt, input_variables=["org", "idea"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=low_llm, temperature=0), prompt=PROMPT)
    eng_script_resp = chain.run(org=str(unique_universities_str), idea=raw_resp.get("IDEA"))
    rst['ENG_script'] = eng_script_resp

    translation_prompt = '''Translate the following English sentence into Chinese. Ensure the translation aligns with typical Chinese expressions and may be adjusted for naturalness and fluency. The result must contain only Chinese words, except for widely recognized English terms in the AI field (such as "token" and "transformer"). You must output only the Chinese translation of the sentence and nothing else. English Sentence: {ori_sentence}'''
    PROMPT = PromptTemplate(
        template=translation_prompt, input_variables=["ori_sentence"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=medium_llm, temperature=0), prompt=PROMPT)
    idea_gpt_resp = chain.run(ori_sentence=raw_resp.get("IDEA"))
    rst['idea'] = idea_gpt_resp

    script_prompt = '''You need to write a script for sharing academic paper in Chinese. The overall tone should be professional, clear, and informative. The style should be suitable for the target audience (college students, professors.) The post should be written in the third person. No extra descriptions or explanations, just the result. 
Here are details:
Author Organization: {org} 
论文核心思想: {idea} 

请以'机构名称 提出/推出/介绍了 xx方法'为句式开头，根据我提供的机构名称灵活撰写内容。注意必须用我提供的机构名称替换'机构名称'
'''
    PROMPT = PromptTemplate(
        template=script_prompt, input_variables=["org", "idea"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=low_llm, temperature=0.5), prompt=PROMPT)
    script_gpt_resp = chain.run(org=rst['university'], idea=rst['idea'])
    rephrase_prompt = '''
            请根据以下文本内容进行优化，去掉无实际意义的套话(例如：该方法旨在xxx、为相关领域的研究提供了xxx等)，同时保留所有关键信息和技术细节。输出结果需条理清晰，适合用于简要描述科研成果或技术方法。你的回复除了润色后的语句，不包括其它任何内容。
待润色讲稿：{script_gpt_resp}
            '''
    PROMPT = PromptTemplate(
        template=rephrase_prompt, input_variables=["script_gpt_resp"],
    )
    rephrase_chain = LLMChain(llm=ChatOpenAI(model_name=low_llm, temperature=0.5), prompt=PROMPT)
    rephrase_resp = rephrase_chain.run(script_gpt_resp=script_gpt_resp)
    rst['script'] = rephrase_resp
    return rst

def author_info_extract(pth, default_model=low_llm, temperature=0, chunk_size=1000):
    loader = PDFMinerLoader(pth)

    def num_tokens_from_string(string: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(string))
        return num_tokens

    data = loader.load()
    raw_content = ''.join([d.page_content for d in data])
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=chunk_size, chunk_overlap=0)
    raw_content = text_splitter.split_text(raw_content)[0]
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

def extract_authors_from_pdf(pdf_path: str):
    authors = author_info_extract(pdf_path)
    if authors is None:
        raise OutputParserException("No authors extracted.")
    processed_authors = []
    for a_i, author in enumerate(authors):
        if len(author) != 2:
            print("Invalid author format, skipping:", author)
            continue
        name, aff = author
        name_clean = name.replace('*', '')
        aff_clean = aff.replace('*', '')
        result = {
            "name": name_clean,
            "affiliation": aff_clean,
        }
        processed_authors.append(result)
    return processed_authors

if __name__ == '__main__':
    demo_addr = github_checker(pdf_path)
    print(f"Start analyzing content...")
    paper_resp = process_paper(
        pdf_pth=pdf_path,
        low_llm=low_llm,
    )
    title = paper_resp.get("title")
    abstract = paper_resp.get("abstract")
    key_idea = paper_resp.get("key_idea")
    fig_caps = paper_resp.get("fig_caps")
    tab_caps = paper_resp.get("tab_caps")
    key_fig = paper_resp.get("key_fig")
    key_tab = paper_resp.get("key_tab")
    raw_resp = paper_resp.get("raw_resp")
    status = paper_resp.get("status")
    authors = extract_authors_from_pdf(pdf_path)

    reading_script_dict = generate_reading_script(paper_resp, authors)
    cn_university = reading_script_dict['university']
    cn_idea = reading_script_dict['idea']
    cn_script = reading_script_dict['script']

    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['paper_id', 'university', 'idea', 'script', 'title', 'abstract', 'oa_access', 'TNCSI']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if csvfile.tell() == 0:
            writer.writeheader()
        writer.writerow({
            'paper_id': paper_id,
            'university': cn_university,
            'idea': cn_idea,
            'script': cn_script,
            'title': title,
            'abstract': abstract.strip().replace('\n', ' '),
            'oa_access': demo_addr,
            'TNCSI': 0,
        })
    df = pd.read_csv(csv_path)
    df_unique = df.drop_duplicates(subset=['paper_id'], keep='first')
    df_unique.to_csv(csv_path, index=False, encoding='utf-8')

    try:
        html = generate_HTML_template(title, authors, demo_addr, cn_script, key_tab, key_fig, publication_date=datetime.datetime.now(), venue='', base_analysis_dir=base_analysis_dir)
        html_template_file = os.path.join(base_analysis_dir, f'{paper_id}.html')
        if html is not None:
            write_string_to_file(html, html_template_file)
            capture_div_screenshot(
                html_template_file,
                os.path.join(base_analysis_dir, f'{paper_id}.png')
            )
    except Exception as e:
        print(e)

