import json

from reduct_db import use_session, PaperDAO

from analyzer.llm_function import create_bilingual_script_dict
from cfg.safe_session import session_factory
from reduct_db.db_entities import Papers, PaperDetails

from cfg.langchain_imports import *


from langchain.prompts import (
    PromptTemplate,
)

from langchain_community.chat_models import ChatOpenAI
from cfg.STATUS import *
from collections import OrderedDict
from retry import retry

from db_services.paper_service import PaperService


@use_session()
def generate_reading_scirpt(paper:Papers, session=None):

    title = paper.title
    abstract = paper.paper_detail.abstract



    eng_affs, cn_affs = PaperService(session).get_affiliation_names_by_paper_id(paper.id)
    print(title,abstract,eng_affs,cn_affs)

    return {}#create_bilingual_script_dict()
@retry(delay=6, tries=3)
def generate_reading_script_deprecated(paper_detail:PaperDetails):
    '''

    :param raw_resp:
    :param default_model:
    :return: {'script':保存script, 'university':大学中文名, 'idea':方法}
    '''

    # raw_resp = paper_detail.raw_resp
    rst = {}
    # raw_resp = json.loads(raw_resp)

    author_response = paper_detail.extract_author_raw_resp
    # print(paper_detail.id)
    authors = json.loads(author_response)
    # 提取所有大学
    # universities = [list(author.values())[0] for author in raw_resp.get("AUTHORS")]

    universities = [] #[author[1].replace('*', '') for author in raw_resp.get("AUTHORS")]
    for author in authors:
        if len(author) == 2:
            universities.append(author[1].replace('*', ''))

    # 去重并保持顺序
    unique_universities = list(OrderedDict.fromkeys(universities))# list(set(universities))

    # 判断机构数量
    if len(unique_universities) > 3:
        unique_universities = unique_universities[:2] + [unique_universities[-1]]
    unique_universities_str = ", ".join(unique_universities)

    university_template = """Given the provided address or affiliation information, identify and extract only the names of the primary institutions such as universities, companies, or main research bodies. Translate these names into Chinese, ensuring accuracy and EXCLUDING any sub-institutions, departments, or specific research centers. Output the translated names in the format: Organization 1, Organization 2, Organization 3. Include only the requested information without any additional content. {universities}"""
    PROMPT = PromptTemplate(
        template=university_template, input_variables=["universities"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=low_llm, temperature=0), prompt=PROMPT)
    # print(unique_universities_str)
    uni_gpt_resp = chain.run(universities = str(unique_universities_str))
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
        template=ENG_script_prompt, input_variables=["org","idea"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=low_llm, temperature=0), prompt=PROMPT)
    eng_script_resp = chain.run(org = str(unique_universities_str), idea = paper_detail.key_idea)
    rst['ENG_script'] = eng_script_resp

    translation_prompt = '''Translate the following English sentence into Chinese. Ensure the translation aligns with typical Chinese expressions and may be adjusted for naturalness and fluency. The result must contain only Chinese words, except for widely recognized English terms in the AI field (such as "token" and "transformer"). You must output only the Chinese translation of the sentence and nothing else. English Sentence: {ori_sentence}'''
    PROMPT = PromptTemplate(
        template=translation_prompt, input_variables=["ori_sentence"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=medium_llm, temperature=0), prompt=PROMPT)
    idea_gpt_resp = chain.run(ori_sentence=paper_detail.key_idea)
    rst['idea'] = idea_gpt_resp

    # script_prompt = f'''请根据如下提供内容撰写一篇用于分享学术论文的简短稿件。整体语言风格清晰、地道、专业，文风应适合目标读者（研究生、教授），内容需使用第三人称表述。
    #     以下是具体信息：
    #     作者机构：{{org}}
    #     论文核心思想：{{idea}}
    #     请以“机构名称 提出/推出/介绍了 xx方法”为句式开头，根据我提供的机构名称灵活撰写内容。注意：
    #     （1）必须用我提供的机构名称替换“机构名称”；
    #     （2）不要编造任何我没提供的信息；
    #     （2）仅根据提供的核心思想介绍方法，不得使用“提供新的思路”、“提供重要资源”等任何评判性或总结性表达，不作任何点评、结论或总结，；
    #     （3）输出仅包含根据核心思想撰写的讲稿内容，不包括其它任何描述或解释。
    #     '''+
    script_prompt = '''You need to write a script for sharing academic paper in Chinese. The overall tone should be profession, clear, and informative. The style should be suitable for the target audience (college students, professors.) The post should be written in the third person. No extra descriptions or explanations, just the result. \n Here are details:\n Author Organization: {org} \n 论文核心思想: {idea} \n
        请以'机构名称 提出/推出/介绍了 xx方法'为句式开头，根据我提供的机构名称灵活撰写内容。注意必须用我提供的机构名称替换'机构名称'
        '''
    PROMPT = PromptTemplate(
        template=script_prompt, input_variables=["org","idea"],
    )
    chain = LLMChain(llm=ChatOpenAI(model_name=low_llm,temperature=0.5), prompt=PROMPT)
    script_gpt_resp = chain.run(org = rst['university'],idea=rst['idea'])
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

if __name__ == '__main__':
    session = session_factory()
    paper = PaperDAO(session).get_by_id(3)
    generate_reading_scirpt(paper)
    # additional_info = ''
    # if paper.authors_title != 0:
    #     # print(paper.authors_title)
    #     additional_info = authors_title_decorator(binary_to_titles(hex_to_binary(paper.authors_title)),type='str')
    # additional_info = '' # 不考虑addition info
    # if additional_info == '':
    #     CN_prompt = '''请以'机构名称 提出/推出/介绍了 xx方法'为句式开头，根据我提供的机构名称灵活撰写内容。注意：（1）必须用我提供的机构名称替换'机构名称'；（2）避免无实际意义的套话，语言简练流畅。'''
    # else:
    #     CN_prompt ='''请模仿句式“某某大学/机构 某某Fellow团队 提出/推出/介绍了xx方法”开头（如foo大学IEEE Fellow团队提出了xxx），灵活地道进行撰写.请注意，某某只是一个代词，你务必使用我提供的机构名称进行替换。'''
    # script_prompt = '''You need to write a script for sharing academic paper in Chinese. The overall tone should be profession, clear, and informative. The style should be suitable for the target audience (college students, professors.) The post should be written in the third person. No extra descriptions or explanations, just the result. \n Here are details:\n Author Organization: {org} \n {author_titles} \n 论文核心思想: {idea} \n
    #   \n {CN_prompt}'''    （2）仅根据提供的核心思想介绍方法，不得使用任何评判性或总结性表达，不作任何点评、结论或总结。；

    # session.query()
    # session = session_factory()
    # papers = session.query(Papers).filter(Papers.cn_script.isnot(None)).all()
    # for p in papers:
    #     script_prompt = '''You need to write a script for sharing academic paper in Chinese. The overall tone should be profession, clear, and informative. The style should be suitable for the target audience (college students, professors.) The post should be written in the third person. No extra descriptions or explanations, just the result. \n Here are details:\n Author Organization: {org} \n 论文核心思想: {idea} \n
    #         请以'机构名称 提出/推出/介绍了 xx方法'为句式开头，根据我提供的机构名称灵活撰写内容。注意必须用我提供的机构名称替换'机构名称'
    #         '''
    #     PROMPT = PromptTemplate(
    #         template=script_prompt, input_variables=["org", "idea"],
    #     )
    #     chain = LLMChain(llm=ChatOpenAI(model_name='gpt-4o-mini-2024-07-18', temperature=0.8), prompt=PROMPT)
    #     script_gpt_resp = chain.run(org=p.cn_university,
    #                                 idea=p.cn_idea)
    #     print(script_gpt_resp)
    #
    #     rephrase_prompt = '''
    #     请根据以下文本内容进行优化，去掉无实际意义的套话(例如：该方法旨在xxx、为相关领域的研究提供了xxx等)，同时保留所有关键信息和技术细节。输出结果需条理清晰，适合用于简要描述科研成果或技术方法。你的回复除了润色后的语句，不包括其它任何内容。
    #     待润色讲稿：{script_gpt_resp}
    #     '''
    #     PROMPT = PromptTemplate(
    #         template=rephrase_prompt,input_variables=["script_gpt_resp"],
    #     )
    #     rephrase_chain = LLMChain(llm=ChatOpenAI(model_name='gpt-4o-mini-2024-07-18', temperature=0.5), prompt=PROMPT)
    #     rephrase_resp = rephrase_chain.run(script_gpt_resp=script_gpt_resp)
    #     print(rephrase_resp)
    #
    #     ENG_script_prompt = f'''Please draft a brief script for sharing an academic paper based on the information provided below. The language style should be clear, professional, and natural, tailored to the target audience (graduate students, professors). The content should be written in the third person.
    #
    #     Details are as follows:
    #     Author Organization: {{org}}
    #     Core Idea of the Paper: {{idea}}
    #
    #     Begin the script with the sentence structure “The [organization name] proposed/introduced/presented the xx method,” replacing “[organization name]” with the organization provided. Notes:
    #     (1) You must replace “[organization name]” with the provided organization name;
    #     (2) Do not fabricate any information not explicitly provided;
    #     (3) Describe the method solely based on the provided core idea. Do not use evaluative or summarizing language such as “offers new insights” or “provides important resources.” Do not include any commentary, conclusions, or summaries;
    #     (4) The output must only contain the draft script based on the core idea, with no additional descriptions or explanations.
    #     '''
    #     PROMPT = PromptTemplate(
    #         template=ENG_script_prompt, input_variables=["org", "idea"],
    #     )
    #     chain = LLMChain(llm=ChatOpenAI(model_name=low_llm, temperature=0), prompt=PROMPT)
    #     # print(unique_universities_str)
    #     raw_resp = p.raw_resp
    #     rst = {}
    #     raw_resp = json.loads(raw_resp)
    #
    #     author_response = p.authors
    #     authors = json.loads(author_response)
    #
    #
    #     universities = []
    #     for author in authors:
    #         if len(author) == 2:
    #             universities.append(author[1].replace('*', ''))
    #
    #     # 去重并保持顺序
    #     unique_universities = list(OrderedDict.fromkeys(universities))  # list(set(universities))
    #
    #     # 判断机构数量
    #     if len(unique_universities) > 3:
    #         unique_universities = unique_universities[:2] + [unique_universities[-1]]
    #     unique_universities_str = ", ".join(unique_universities)
    #     eng_script_resp = chain.run(org=str(unique_universities_str), idea=p.key_idea)
    #     print(eng_script_resp)
    #     print('\n\n\n')
    # script_gpt_resp = chain.run(org = '新加坡国立大学, 华为技术有限公司',idea='该论文介绍了Vista3D，这是一个采用两阶段方法从单个图像生成3D对象的框架，利用高斯喷洒进行粗略几何建模和有符号距离函数进行细节处理，通过解耦纹理表示和角度扩散先验合成进行增强。')
    # print(script_gpt_resp)
    # script_gpt_resp = chain.run(org = '伦敦国王学院生物医学工程与成像科学学院, 伦敦国王学院; HeartFlow公司, 伦敦帝国学院; HeartFlow公司, 伦敦国王学院生物医学工程与成像科学学院; 浙江师范大学数学医学学院.',idea='该论文提出了一种方法，结合了切片移位算法（SSA）、空间变换网络（STN）和标签变换网络（LTN），用于纠正分割的心脏磁共振（CMR）切片中的呼吸运动，并将稀疏分割数据转换为密集分割，以改善三维整个心脏几何重建。')
    # print(script_gpt_resp)
    # script_gpt_resp = chain.run(org = '安徽大学计算机科学与技术学院, 安徽大学, 安徽中医药大学第一附属医院.',idea='该论文介绍了一种名为R2GenCSR的新型上下文引导高效X射线医疗报告生成框架，该框架利用猛犸视觉骨干进行线性复杂特征提取，并从训练集中实现上下文检索，以增强特征表示和区分性学习，从而实现高质量的医疗报告生成。')
    # print(script_gpt_resp)
    # script_gpt_resp = chain.run(org = '俄勒冈州立大学, Adobe研究.',idea='该论文介绍了PointRecon，一种在线基于点的3D重建方法，它保持全局点云表示，并使用一种新颖的基于射线的2D-3D特征匹配技术，用于在观察到新图像时实时更新点特征并预测深度。')
    # print(script_gpt_resp)