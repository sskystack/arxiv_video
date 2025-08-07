from collections import OrderedDict

from cfg.STATUS import *
from cfg.langchain_imports import *
from logs.loggers import arxiv_logger
from analyzer.parser import *





def binary_to_hex(binary_str):
    # 将二进制字符串转换为整数
    decimal = int(binary_str, 2)
    # 将整数转换为十六进制字符串并去掉前缀'0x'
    hex_str = hex(decimal)[2:]
    return hex_str.upper()  # 返回大写形式的十六进制字符串





prompt = PromptTemplate(
    template="Answer the user query.\n{format_instructions}\n{query}\n",
    input_variables=["query"],
    partial_variables={"format_instructions": lpqa_parser.get_format_instructions()},
)


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(low_llm)
    num_tokens = len(encoding.encode(string))
    return num_tokens

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
        arxiv_logger.warning(f'Idea parser exception {e}')

        fix_parser = OutputFixingParser.from_llm(parser=idea_parser, llm=ChatOpenAI(model_name=medium_llm, temperature=0))

        p_rst = fix_parser.parse(rst)

        print(f'fixed output {p_rst}')
    return p_rst

def single_paper_info_extract(abstract, pdf_pth,default_model=low_llm, temperature=0):


    idea_rst = get_key_idea(abstract, default_model=default_model, temperature=temperature,lang='zh')
    fig_tab_rst = get_figs_tabs(pth=pdf_pth, default_model=default_model, temperature=temperature)

    # loader = PDFMinerLoader(pdf_pth)
    # data = loader.load()
    # raw_content = ''.join([d.page_content for d in data])
    # text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=20000, chunk_overlap=0)
    # raw_content = text_splitter.split_text(raw_content)[0]
    # arxiv_logger.info(f'Analyzing this paper cost {num_tokens_from_string(raw_content)} tokens')

    single_paper_info_entity =  Paper_Info_Entity()
    single_paper_info_entity.FIGURE_CAPTION = fig_tab_rst.FIGURE_CAPTION
    single_paper_info_entity.TABLE_CAPTION = fig_tab_rst.TABLE_CAPTION
    single_paper_info_entity.IDEA = idea_rst.IDEA

    return single_paper_info_entity

# @retry(OutputParserException,tries=2)
def longtext_paper_qa(pth, arxiv_logger, default_model=medium_llm, temperature=0, debug=False):
    loader = PDFMinerLoader(pth)

    def num_tokens_from_string(string: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model(medium_llm)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    data = loader.load()
    raw_content = ''.join([d.page_content for d in data])
    # 使用 CharacterTextSplitter 分割文本

    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=20000, chunk_overlap=0)
    raw_content = text_splitter.split_text(raw_content)[0]
    arxiv_logger.info(f'Analyzing this paper cost {num_tokens_from_string(raw_content)} tokens')

    prompt_template = """
    [Step 1 of 4] Find all the figure captions in the paper, you may pay attention to text like "Fig. X" or "Figure. X".

    [Step 2 of 4] Find all the table captions in the paper, you may pay attention to text like "Tab. X" or "Table. X".

    [Step 3 of 4] I need a concise summary of the core method proposed in this paper. Could you distill the provided paper into a single, clear sentence?

    [Step 4 of 4] Now, check if the authors have mentioned sharing their code, dataset, or something related on the website? Pay attnetion to sentences like 'Code is released at xxx', 'Project page is xxx', etc. If so, please list these links. 

    \nProvided paper: {context}\n
    Format Instructions:\n{format_instructions}
     """
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context"],
        partial_variables={"format_instructions": lpqa_parser.get_format_instructions()},
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature, max_tokens=4096), prompt=PROMPT)

    rst = chain.run(context=raw_content)

    try:
        p_rst = lpqa_parser.parse(rst)
    except OutputParserException as e:
        print(f'raw output {rst}')
        arxiv_logger.warning(f'Response parse error in longtext_paper_qa.')
        fix_parser = OutputFixingParser.from_llm(parser=parser_fix, llm=ChatOpenAI(model_name=medium_llm, temperature=0))
        p_rst = fix_parser.parse(rst)
        print(f'fixed output {p_rst}')
    return p_rst

def check_fellow_from_bio_intrst(bio):
    output_parser = CommaSeparatedListOutputParser()
    format_instructions = output_parser.get_format_instructions()
    template = '''Given the biography provided, determine if the subject of the biography holds any of the following titles or affiliations, and represent the presence of each with a binary digit (1 for present, 0 for absent). The titles are ordered as follows: IEEE Fellow, IAPR Fellow, ACM Fellow, SPIE Fellow, 杰出青年 (Distinguished Young Scholar), 优秀青年 (Excellent Young Scientist), 长江学者 (Chang Jiang Scholar), 院士 (National Academy Member). Format the output as an 8-digit binary number, where each digit corresponds to a title, in the order listed.

    Please focus only on the subject of the biography. You MUST disregard any titles or affiliations mentioned that pertain to collaborators or other individuals. For IEEE, IAPR, ACM, and SPIE, only recognize the title of "Fellow." Do NOT count general memberships, senior memberships, or other affiliations as equivalent titles.
    
    Provided Biography: {bio}
    
    Example output format for a subject who is an IEEE Fellow and a Distinguished Young Scholar would be '10001000'. For a subject who is a National Academy Member only, the output would be '00000001'.
    
    You should only reply with binary integer numbers. NO OTHER WORDS ARE ALLOWED.
 '''
    prompt_template = PromptTemplate(input_variables=["bio"], template=template)

    # llm = Ollama(model="llama3", num_predict=400, num_ctx=2048, temperature=0.5,num_thread=6, top_k=1, top_p=0.2, keep_alive='2m',mirostat=2,mirostat_eta=0.1,mirostat_tau=8,stop=['<|eot_id|>'])
    llm = ChatOpenAI(temperature=0, model=low_llm)
    chain = LLMChain(llm=llm, prompt=prompt_template, output_key='bio')
    bio = chain.run(bio)
    return str(binary_to_hex(bio))

# def judge_key_figure(fig_caps, default_model=low_llm, temperature=0):
#     if len(fig_caps) == 0:
#         return -1
#     if len(fig_caps) == 1:
#         return 0
#     prompt_template = """
#     Below are all the figure captions from an article, and you need to determine which one is the main figure based on these captions. The main figure typically refers to a flowchart of methods, framework diagram, model structure chart, etc. Since I will use your response directly in subsequent programs, your reply must contain only one number, which is the sequence number of the picture (start from 1).
#     \n\n{caps}
#      """
#     caps = '; '.join(fig_caps)
#
#     PROMPT = PromptTemplate(
#         template=prompt_template, input_variables=["caps"]
#     )
#     chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)
#     rst = chain.run(caps=caps)
#     try:
#         rst = int(rst) - 1
#         if rst <0:
#             raise ValueError
#     except:
#         return 0
#     return rst

def judge_key_figure_by_id(fig_items: list, default_model=low_llm, temperature=0):
    """
    fig_items: List of tuples (id, caption)
    Returns: the selected main figure id (str) or None if failed
    """
    if len(fig_items) == 0:
        return None
    if len(fig_items) == 1:
        return fig_items[0][0]  # 只有一个，直接返回id

    fig_list_text = "\n".join([f"ID: {fid} | Caption: {caption}" for fid, caption in fig_items[:10]])
    valid_ids = [fid for fid, _ in fig_items]

    prompt_template = """
    You are given a list of figure IDs and their captions from a scientific article, formatted as (ID: Caption).

    Your task is to identify the one figure that best represents the proposed method or framework, such as a model architecture diagram, workflow chart, or system overview.

    Here are the figures:
    {fig_list_text}

    Format Instructions:
    {format_instructions}
    """

    PROMPT = PromptTemplate(
        template=prompt_template.strip(),
        input_variables=["fig_list_text"],
        partial_variables={"format_instructions": ve_parser.get_format_instructions()}
    )

    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)

    try:
        raw_response = chain.run(fig_list_text=fig_list_text)
        parsed_response = ve_parser.parse(raw_response)
        selected_id = parsed_response.ID

        if selected_id in valid_ids:
            return selected_id
        else:
            print(f"[⚠️警告] LLM返回了非法ID: {selected_id}")
            return valid_ids[0]  # 返回第一个兜底
    except Exception as e:
        print(f"[❌错误] judge_key_figure_by_id 解析失败: {e}")
        return valid_ids[0]


def judge_key_table_by_id(tab_items: list, default_model=low_llm, temperature=0):
    """
    tab_items: List of tuples (id, caption)
    Returns: the selected main table id (str) or None if failed
    """
    if len(tab_items) == 0:
        return None
    if len(tab_items) == 1:
        return tab_items[0][0]  # 只有一个，直接返回id

    tab_list_text = "\n".join([f"ID: {tid} | Caption: {caption}" for tid, caption in tab_items[:10]])
    valid_ids = [tid for tid, _ in tab_items]

    prompt_template = """You are given a list of table IDs and their captions from a scientific article (ID: Caption).

    Your task is to pick the table that most likely reports core performance results supporting the paper’s main claim.

    Look for captions suggesting:
    - overall method performance,
    - comparisons to baselines or prior work,
    - evaluation on main tasks or datasets.

    Rules:
    - Only choose from provided IDs exactly as shown.
    - Do not create or modify IDs.
    - Output exactly one ID in this format:

    Here are the tables:
    {tab_list_text}

    {format_instructions}
    """

    PROMPT = PromptTemplate(
        template=prompt_template.strip(),
        input_variables=["tab_list_text"],
        partial_variables={"format_instructions": ve_parser.get_format_instructions()}
    )

    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)

    try:
        raw_response = chain.run(tab_list_text=tab_list_text)
        parsed_response = ve_parser.parse(raw_response)
        selected_id = parsed_response.ID

        if selected_id in valid_ids:
            return selected_id
        else:
            print(f"[⚠️警告] LLM返回了非法ID: {selected_id}")
            return valid_ids[0]  # 返回第一个兜底
    except Exception as e:
        print(f"[❌错误] judge_key_table_by_id 解析失败: {e}")
        return valid_ids[0]

def judge_key_table(tab_caps, default_model=low_llm, temperature=0):
    if len(tab_caps) == 0:
        return -1
    if len(tab_caps) == 1:
        return 0
    prompt_template = """
    Below are all the table captions from an article, and you need to determine which one is the most important table based on these captions. Typically, this would be a table comparing the proposed method with other approaches to show its superiority. Since I will use your response directly in subsequent programs, your reply must contain only one number, which is the sequence number of the table (start from 1).
    \n\n{caps}
     """
    caps = '; '.join(tab_caps )
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["caps"]
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)
    rst = chain.run(caps=caps)
    try:
        rst = int(rst) - 1
        if rst <0:
            raise ValueError
    except:
        return 0
    return rst

def get_benchmark(gpt_response, default_model='moonshot-v1-8k', temperature=0):
    benchmark_md = gpt_response.TABLE_CONTENT

    class Benchmark(BaseModel):
        BENCHMARK: List[Dict[str, float]] = Field(
            description="List of performance scores for different methods in the provided table. Each entry in the list should be formatted as [{'method name': performance score}, ...]. e.g. [{'ResNet'}:': 78.6, {'ViT'}:': 80.6]. Make sure the last entry corresponds to the proposed method. If the performance score contains any non-numerical elements, then remove this item to ensure the format meets the requirements. "
        )

    parser = PydanticOutputParser(pydantic_object=Benchmark)
    prompt_template = """
    The table below is characterized by comparing the proposed method with other methods, aiming to highlight the superiority of the proposed approach. You need to identified the most important metric and dataset used in this table based on your understanding. Report the performance of different methods from the main comparative experimental table only. If the table involves multiple datasets or multiple evaluation metrics, you only need to report the results of all different methods on the most important dataset using the most important metric.
    \n\n{benchmark_md} \n\n {format_instructions}
     """
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["benchmark_md"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)
    rst = chain.run(benchmark_md=benchmark_md)
    # print(parser.parse(rst))
    return parser.parse(rst).BENCHMARK
import re
def filter_list(input_list,pattern = r'\b(Fig\.?|Figure|FIG|FIGURE)\b'): # r'\b(Table|TAB|TABLE|Tab\.)\b'
    # 编译一个正则表达式模式来检查包含 'www.'、'http:'、'https:' 等子串的内容
    # pattern = re.compile(r'www\.|http:|https:|\.com|github|sway')
    pattern = re.compile(pattern, re.IGNORECASE)
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
    rst = {'fig':filter_list(texts, r'\b(Fig\.?|Figure|FIG|FIGURE)\b'), 'tab': filter_list(texts,r'\b(Table|TAB|TABLE|Tab\.)\b')}
    return rst

def get_figs_tabs(pth, default_model="gpt4o-mini", temperature=0,):
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


def get_university_country_by_gpt(university_name, default_model=low_llm, temperature=0):
    prompt_template = f"""
    Please tell me the country where this institution is located. Note that your response must contain only the name of the country and nothing else. If you cannot determine it, reply with "None".
    \n\n{university_name}
     """
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["university_name"])
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)
    rst = chain.run(university_name=university_name)
    if rst == 'None':
        return None
    else:
        return rst

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from retry import retry
@retry()
def get_chatgpt_field(title, abstract=None, sys_content=None, usr_prompt=None, extra_prompt=True,model="gpt-3.5-turbo-0125",temperature=0):

    if not sys_content:
        sys_content = (
            "You are a profound researcher who is good at identifying the topic key phrase from paper's title and "
            "abstract. Ensure that the topic key phrase precisely defines the research area within the article. For effective academic searching, such as on Google Scholar, the field should be specifically targeted rather than broadly categorized. For instance, use 'image classification' instead of the general 'computer vision' to enhance relevance and searchability of related literature.")
    if not usr_prompt:
        usr_prompt = ("Given the title and abstract below, determine the specific research field by focusing on the main application area and the key technology. You MUST respond with the keyword ONLY in this format: xxx")

    messages = [SystemMessage(content=sys_content)]

    extra_abs_content = '''
    Given Title: Large Selective Kernel Network for Remote Sensing Object Detection
    Given Abstract: Recent research on remote sensing object detection has largely focused on improving the representation of oriented bounding boxes but has overlooked the unique prior knowledge presented in remote sensing scenarios. Such prior knowledge can be useful because tiny remote sensing objects may be mistakenly detected without referencing a sufficiently long-range context, which can vary for different objects. This paper considers these priors and proposes the lightweight Large Selective Kernel Network (LSKNet). LSKNet can dynamically adjust its large spatial receptive field to better model the ranging context of various objects in remote sensing scenarios. To our knowledge, large and selective kernel mechanisms have not been previously explored in remote sensing object detection. Without bells and whistles, our lightweight LSKNet sets new state-of-the-art scores on standard benchmarks, i.e., HRSC2016 (98.46% mAP), DOTA-v1.0 (81.85% mAP), and FAIR1M-v1.0 (47.87% mAP).''' if abstract else ''
    if extra_prompt:
        messages += [HumanMessage(content=f'''{usr_prompt}\n\n{extra_abs_content}'''), AIMessage(content='remote sensing object detection')]

    content = f'''{usr_prompt}
                Given Title: {title}
            '''
    if abstract:
        content += f'Given Abstract: {abstract}'
    messages.append(HumanMessage(content=content))

    chat = ChatOpenAI(model=model,temperature=temperature)



    return chat.batch([messages])[0].content

@retry()
def get_chatgpt_fields(title, abstract=None, sys_content=None, usr_prompt=None, extra_prompt=True,model="gpt-3.5-turbo-0125",temperature=0):

    if not sys_content:
        sys_content = (
            "You are a profound researcher who is good at identifying the topic key phrase from paper's title and "
            "abstract. Ensure that the topic key phrase precisely defines the research area within the article. For effective academic searching, such as on Google Scholar. Avoid using overly general terms like 'deep learning'"
            ",'image processing', 'Deep neural network'. or 'surveys', etc. And avoid overly specific technical names like 'ResNet', 'Swin Transformer', or 'DiT.' Instead, use broader terms such as 'CNN,','Transformer', or 'Diffusion Models'")
    if not usr_prompt:
        usr_prompt = ("Given the title and abstract below, determine the specific research fields by focusing on the main application area and the key technology. You MUST respond with up to 3 keywords strictly following this format: xxx, xxx, xxx")

    messages = [SystemMessage(content=sys_content)]

    extra_abs_content = '''
    Given Title: RSGaussian:3D Gaussian Splatting with LiDAR for Aerial Remote Sensing Novel View Synthesis
    Given Abstract: This study presents RSGaussian, an innovative novel view synthesis (NVS) method for aerial remote sensing scenes that incorporate LiDAR point cloud as constraints into the 3D Gaussian Splatting method, which ensures that Gaussians grow and split along geometric benchmarks, addressing the overgrowth and floaters issues occurs. Additionally, the approach introduces coordinate transformations with distortion parameters for camera models to achieve pixel-level alignment between LiDAR point clouds and 2D images, facilitating heterogeneous data fusion and achieving the high-precision geo-alignment required in aerial remote sensing. Depth and plane consistency losses are incorporated into the loss function to guide Gaussians towards real depth and plane representations, significantly improving depth estimation accuracy. Experimental results indicate that our approach has achieved novel view synthesis that balances photo-realistic visual quality and high-precision geometric estimation under aerial remote sensing datasets. Finally, we have also established and open-sourced a dense LiDAR point cloud dataset along with its corresponding aerial multi-view images, AIR-LONGYAN.'''
    if extra_prompt:
        messages += [HumanMessage(content=f'''{usr_prompt}\n\n{extra_abs_content}'''), AIMessage(content='Novel View Synthesis, 3D Gaussian Splatting, Aerial Remote Sensing')]

    content = f'''{usr_prompt}
                Given Title: {title}
            '''
    if abstract:
        content += f'Given Abstract: {abstract}'
    messages.append(HumanMessage(content=content))

    chat = ChatOpenAI(model=model,temperature=temperature)



    return chat.batch([messages])[0].content
@retry()
def get_domain_tech_kwds(title, abstract=None, sys_content=None, usr_prompt=None, extra_prompt=True,
                         model="gpt-3.5-turbo-0125", temperature=0):
    if not sys_content:
        sys_content = (
            "You are a profound researcher who is good at conduct a literature review based on given title and abstract."        )
    if not usr_prompt:
        usr_prompt = (
            "Given the title and abstract of a paper, please generate exactly 3 specific and precise keywords for "
            "searching highly related papers on Google Scholar or Semantic Scholar. The first keyword must represent "
            "the paper's main research or application area, while the second and third keywords should reflect the "
            "key techniques or methodologies used. Avoid using overly general terms like 'deep learning,"
            "' 'image processing,' or 'surveys,' and avoid overly specific technical names like 'ResNet,' 'Effective "
            "ViT,' or 'Diffusion ViT.' Instead, use broader terms such as 'CNN,' 'ViT,' or 'Diffusion.' Provide the "
            "keywords in descending order of relevance, formatted as follows: xxx,xxx,xxx.")
    messages = [SystemMessage(content=sys_content)]

    # Prepare the content for the prompt
    content = f'''{usr_prompt}
                Given Title: {title}
            '''
    if abstract:
        content += f'Given Abstract: {abstract}'

    messages.append(HumanMessage(content=content))

    # Use the OpenAI chat model to generate a response
    chat = ChatOpenAI(model=model, temperature=temperature)

    # Extract the response from the chat
    response = chat(messages)


    return response.content



def translate_eng_aff(eng_aff_name, default_model=medium_llm, temperature=0):
    prompt_template = """请将以下英文机构名称翻译为其在中文语境下的正式名称，如果有公认译名请使用该名称。仅输出翻译后的名称本身，不要添加任何解释、标点或其它内容。机构名称：{org}"""
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["org"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature, max_tokens=1024), prompt=PROMPT)
    rst = chain.run(org=eng_aff_name)
    return rst









@retry(delay=6, tries=3)
def create_bilingual_script_dict(title, abstract, eng_affs:list, cn_affs:list, default_model=medium_llm, temperature=0):
    '''

    :param raw_resp:
    :param default_model:
    :return: {'script':保存script, 'university':大学中文名, 'idea':方法}
    '''

    # raw_resp = paper_detail.raw_resp
    rst = {}

    # 去重并保持顺序
    eng_affs = list(OrderedDict.fromkeys(eng_affs))
    cn_affs = list(OrderedDict.fromkeys(cn_affs))
    rst['CN_affs'] = cn_affs
    rst['ENG_affs'] = eng_affs

    eng_affs = eng_affs[:2] + [eng_affs[-1]]
    cn_affs = cn_affs[:2] + [cn_affs[-1]]

    eng_affs_str = ', '.join(eng_affs)
    cn_affs_str = ', '.join(cn_affs)

    ENG_script_prompt = '''Please write a concise script (only one sentence) for presenting an academic paper based on the information below. The language should be clear, professional, and natural, suitable for an academic audience (e.g., graduate students, researchers, professors). Use third-person narration.

    Start the script with the sentence: “The [organization name] proposed/introduced/presented the [method or approach], ” replacing [organization name] with the provided institution name.

    Use only the information provided. Do not add, infer, or fabricate any content. Focus exclusively on the core method or idea described in the abstract. Avoid any evaluative, subjective, or summarizing language (e.g., “novel,” “important,” “valuable”).

    Output must strictly meet the following conditions:
    1. The script must begin with the required sentence structure.
    2. The entire script must ONLY contain **ONE Sentence**.
    3. Do not include any commentary, interpretation, or conclusion.
    4. Output only the generated script. Do not add explanations or formatting.

    Input:
    - Paper Title: {title}
    - Author Organization: {org}
    - Abstract: {abstract} '''
    PROMPT = PromptTemplate(
        template=ENG_script_prompt, input_variables=["org", "title", "abstract"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)
    eng_script_resp = chain.run(org=eng_affs_str, title=title, abstract=abstract)
    rst['ENG_script'] = eng_script_resp

    CN_script_prompt = '''根据提供的信息，撰写一句用于分享英文科研论文的方法一句话介绍讲稿。讲稿必须为**中文**，语气专业、简洁清晰、信息密度高，适合本科生、研究生、教授等学术受众。使用第三人称撰写。

    严格遵守以下要求：

    1. 以“[机构名称] 提出/推出/介绍了 XX方法，”开头，用提供的机构名称替换“[机构名称]”；
    2. 讲稿仅包含一句话，简洁清晰；
    3. 严禁添加、推测或总结任何未提供的信息；
    4. 禁止使用无实际意义的主观套话，如“展现前景”、“为相关领域提供了参考”等；
    5. 可以保留广泛使用的英文AI术语，例如 token、transformer 等；
    6. 输出只包含润色后的中文讲稿，不附加任何说明或解释。

    以下是输入信息：
    - 论文标题: {title}
    - 论文作者机构: {org}
    - 摘要或方法核心思想: {abstract}'''
    PROMPT = PromptTemplate(
        template=CN_script_prompt, input_variables=["org", "title", "abstract"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)
    cn_script_resp = chain.run(org=cn_affs_str, title=title, abstract=abstract)
    rst['CN_script'] = cn_script_resp

    CN_script_prompt = '''你是一位专业的学术论文翻译人员，负责将英文论文的摘要翻译为中文。请严格遵守以下要求：
    1. 翻译必须忠实原意，术语准确，表达严谨；
    2. 使用正式、通顺的中文学术语言，符合科研写作规范；
    3. 不得添加、删减或改写原文信息，不得进行主观总结或解释；
    4. 如遇 transformer、token 等已被广泛接受的术语，可保留英文原文；
    5. 输出仅包含翻译后的**中文摘要**，不包含任何额外说明、格式提示或附加内容。
    
    以下是需要翻译的英文摘要：
    
    {abstract}
    
    请将上方英文摘要翻译为中文，仅输出翻译后的**中文摘要**。'''
    PROMPT = PromptTemplate(
        template=CN_script_prompt, input_variables=["abstract"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=default_model, temperature=temperature), prompt=PROMPT)
    CN_abstract= chain.run(abstract=abstract)
    rst['CN_abstract'] = CN_abstract

    return rst
def translate_keyword(keyword, field='计算机科学',low_llm="gpt-4o-mini"):
    # 优化后的 Prompt 模板，包含术语保留规则
    prompt_template = """
    请将以下{field}领域的英文关键词翻译为中文，输出只包含中文翻译，无需解释或多余内容。

    翻译要求：
    - 请翻译为准确、通顺的中文，如已经存在广为认知的翻译名称，请使用该翻译名称。
    - 如果是普遍知晓的技术术语缩写或专有名词缩写，不要翻译，返回缩写。
    - 请只输出翻译后的中文，不要添加标点或注释。

    英文关键词：{keyword}
    """

    PROMPT = PromptTemplate(
        template=prompt_template.strip(),
        input_variables=["field","keyword",],
    )

    chain = LLMChain(
        llm=ChatOpenAI(model_name=low_llm, temperature=0),
        prompt=PROMPT,
    )

    response = chain.run(keyword=keyword.strip(), field=field)
    return response.strip()


if __name__ == '__main__':
    from cfg.config import *
#     rst = create_bilingual_script_to_db(title='''PartRM: Modeling Part-Level Dynamics with Large Cross-State Reconstruction Model''',abstract=''''As interest grows in world models that predict future states from current
# observations and actions, accurately modeling part-level dynamics has become
# increasingly relevant for various applications. Existing approaches, such as
# Puppet-Master, rely on fine-tuning large-scale pre-trained video diffusion
# models, which are impractical for real-world use due to the limitations of 2D
# video representation and slow processing times. To overcome these challenges,
# we present PartRM, a novel 4D reconstruction framework that simultaneously
# models appearance, geometry, and part-level motion from multi-view images of a
# static object. PartRM builds upon large 3D Gaussian reconstruction models,
# leveraging their extensive knowledge of appearance and geometry in static
# objects. To address data scarcity in 4D, we introduce the PartDrag-4D dataset,
# providing multi-view observations of part-level dynamics across over 20,000
# states. We enhance the model's understanding of interaction conditions with a
# multi-scale drag embedding module that captures dynamics at varying
# granularities. To prevent catastrophic forgetting during fine-tuning, we
# implement a two-stage training process that focuses sequentially on motion and
# appearance learning. Experimental results show that PartRM establishes a new
# state-of-the-art in part-level motion learning and can be applied in
# manipulation tasks in robotics. Our code, data, and models are publicly
# available to facilitate future research.''',cn_affs=['清华大学', '北京大学'],eng_affs=['Tsinghua University','Peking University'])
#     print(rst)
    # import datetime
    # from sqlalchemy import func
    # from cfg.safe_session import session_factory
    # def current_day_data(ID=ResultStatus.SUCCESS, date: datetime = None, session=session_factory()):
    #     from reduct_db.db_entities import Papers
    #     if ID is not None:
    #         if date is None:
    #
    #             results = session.query(Papers).filter(Papers.valid == ID,
    #                                                          func.date(Papers.download_date) == now.date()).all()
    #         else:
    #             results = session.query(Papers).filter(Papers.valid == ID,
    #                                                          func.date(Papers.download_date) == date.date()).all()
    #         return results
    #     else:
    #         if date is None:
    #
    #             results = session.query(Papers).filter(func.date(Papers.download_date) == now.date()).all()
    #         else:
    #             results = session.query(Papers).filter(func.date(Papers.download_date) == date.date()).all()
    #         return results
    # papers = current_day_data(date=datetime.datetime(2024, 12, 25))
    # for paper in papers:
    #     print('='*50)
    #     title = paper.title
    #     abstract = paper.abstract
    #     print(f'Title: {title}')
    #     print(f'Abstract: {abstract}')
    #     print(get_domain_tech_kwds(title, abstract,))