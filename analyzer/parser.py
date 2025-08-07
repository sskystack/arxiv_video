import requests_cache
from langchain_openai.chat_models import ChatOpenAI

from cfg.STATUS import medium_llm

# 配置 requests_cache，使用 SQLite 后端
requests_cache.install_cache('demo_cache')

from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field
from typing import List, Tuple
from typing import Dict

import langchain

# import langchain.chains.retrieval_qa.base

langchain.debug = False

import ssl

ssl._create_default_https_context = ssl._create_unverified_context


class GPT_Paper_Response_lstauthor(BaseModel):
    # AUTHORS: List[List[str]] = Field(
    #     description="Author name and the corresponding affiliation's full name. Please provide the official name of the institution only, excluding any labs, departments, country or regional names, as well as any abbreviations or postal codes. Format the answer like [[Name, Affiliation], [Name, Affiliation],...], e.g. [['Yann LeCun', 'New York University'], ...]. Add an asterisk (*) after the name of the communicating author if you can confirm it.")
    FIGURE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all figures in the order they actually appear in the document. If the caption is too long, you can keep only the first sentence of the caption for each image. Format your answer like ['Fig. 1: CAPTION', 'Fig. 2: CAPTION', ...].")
    TABLE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all tables in the order they actually appear in the document. If the caption is too long, you can keep only the first sentence of the caption for each table. Format your answer like ['Tab. 1: CAPTION', 'Tab. 2: CAPTION', ...].")
    IDEA: str = Field(
        description="A concise summary of the core method proposed in this paper. To answer this question, you MUST NOT refer to the abstract and the conclusion section")
    OA: List[str] = Field(
        description="Links to the proposed open-source code or datasets of the given paper? Links mentioned in the reference list can not be the answer. Format the answer like ['https://xxx', ...]. If no proposed open-source code or datasets are reported, output as []")

    # TABLE_CONTENT: str = Field(description="""The content of the table that you think best showcases the superiority of the proposed method compared to other methods. The content of the table typically involves comparative experiments. The content should be re-formatted in Markdown format.  For example, '|Method | Latency| Mobile | Top-1  Accuracy | \\n
    #         |---|---|---|---|
    # |Example method 1 | 2.6 | | 5.43 | 66.2 |
    # |Example method 2(ours) | 2.7 | 5.67 | 69.4 |' """)
class GPT_Paper_Response_Fixer(BaseModel):
    # AUTHORS: List[List[str]] = Field(
    #     description="Author name and the corresponding affiliation's full name. Please provide the official name of the institution only, excluding any labs, departments, country or regional names, as well as any abbreviations or postal codes. Format the answer like [[Name, Affiliation], [Name, Affiliation],...], e.g. [['Yann LeCun', 'New York University'], ...]. Add an asterisk (*) after the name of the communicating author if you can confirm it.")
    FIGURE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all figures in the order they actually appear in the document. e.g. ['Fig. 1: The network architecture framework', 'Fig. 2: Visualization results', ...]")
    TABLE_CAPTION: List[str] = Field(
        description="Regardless of any formatting issues, list the captions of all tables in the order they actually appear in the document. e.g. ['Tab. 1: Comparision with SOTA methods', 'Tab. 2: Abalation Study', ...]")
    IDEA: str = Field(description="A concise summary of the core method proposed in this paper.")
    OA: List[str] = Field(
        description="Links to the open-source code or datasets of provided paper. The answer should be formatted like ['link1','link2', ...]. ")
    # TABLE_CONTENT: str = Field(description="""The content of the table that you think best showcases the superiority of the proposed method compared to other methods. The content of the table typically involves comparative experiments. The content should be re-formatted in Markdown format.  """)



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


# class GoogleScholarUser(BaseModel):
#     USER_INFO: Tuple[str, str, str, int] = Field(
#         description="Stores the tuple (user_ID, Name, Affiliation, Received Citation Count) "
#                     "as retrieved directly. This allows for direct parsing from provided scholarly information. If you can find the author, formet the answer like ('{user_id}','{name}','{affiliation}', '{Citation Count}'). If there is no specific author from the designated affiliation, answer with ('None','None','None',-1)"
#     )
#

class GoogleScholarUser(BaseModel):
    UID: str = Field(
        description="The UID of the matched scholar."
    )
    NAME: str = Field(
        description="The name of the matched scholar."
    )
    INSTITUTION: str = Field(
        description="The Institution of the matched scholar."
    )
    CITES: int = Field(
        description="The received cites of the matched scholar."
    )

class Author_Response(BaseModel):
    AUTHORS: List[List[str]] = Field(
        description="Provide the official name of each author and their corresponding institution in the following "
                    "format: [[Name, Affiliation], [Name, Affiliation], ...]. Use the full, official name of the "
                    "institution only, excluding any sub-affiliations (e.g., DARPA Labs, Tencent Labs), departments ("
                    "e.g., College of Computer Science), countries, regions, abbreviations, or postal codes. Format your answer like"
                    "[['Yann LeCun', 'New York University'], [Sam Altman, OpenAI] ...].")
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

class OA_QUICK_PARSER(BaseModel):
    OA: List[str] = Field(
        description="Links to the proposed open-source code or datasets. Links mentioned in the reference list can not be the answer. Format the answer like ['link1','link2',...,]. If no proposed open-source code or datasets are reported, output as []")

class FigTabID_Response(BaseModel):
    ID: str = Field(
        description="The ID of the selected main figure or tables. Only choose from the provided IDs.."
    )




# parser
gsu_parser = PydanticOutputParser(pydantic_object=GoogleScholarUser)
lpqa_parser = PydanticOutputParser(pydantic_object=GPT_Paper_Response)
lpqa_parser_lstauthor = PydanticOutputParser(pydantic_object=GPT_Paper_Response_lstauthor)
parser_fix = PydanticOutputParser(pydantic_object=GPT_Paper_Response_Fixer)
author_parser = PydanticOutputParser(pydantic_object=Author_Response)
fig_tab_parser = PydanticOutputParser(pydantic_object=Fig_Tab_Response)
idea_parser = PydanticOutputParser(pydantic_object=Idea_Response)
oa_parser = PydanticOutputParser(pydantic_object=OA_Response)
paper_info_parser = PydanticOutputParser(pydantic_object=Paper_Info_Response)
ve_parser = PydanticOutputParser(pydantic_object=FigTabID_Response)

# fixer
gsu_parser = OutputFixingParser.from_llm(parser=gsu_parser, llm=ChatOpenAI(model_name=medium_llm, temperature=0))
lpqa_parser = OutputFixingParser.from_llm(parser=lpqa_parser, llm=ChatOpenAI(model_name=medium_llm, temperature=0))
lpqa_parser_lstauthor = OutputFixingParser.from_llm(parser=lpqa_parser_lstauthor, llm=ChatOpenAI(model_name=medium_llm, temperature=0))
author_parser = OutputFixingParser.from_llm(parser=author_parser, llm=ChatOpenAI(model_name=medium_llm, temperature=0))
fig_tab_parser = OutputFixingParser.from_llm(parser=fig_tab_parser, llm=ChatOpenAI(model_name=medium_llm, temperature=0))
idea_parser = OutputFixingParser.from_llm(parser=idea_parser, llm=ChatOpenAI(model_name=medium_llm, temperature=0))
oa_parser = OutputFixingParser.from_llm(parser=oa_parser, llm=ChatOpenAI(model_name=medium_llm, temperature=0))
paper_info_parser = OutputFixingParser.from_llm(parser=paper_info_parser, llm=ChatOpenAI(model_name=medium_llm, temperature=0))
ve_parser = OutputFixingParser.from_llm(parser=ve_parser, llm=ChatOpenAI(model_name=medium_llm, temperature=0))