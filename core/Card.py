import re
from reduct_db.db_config.safe_session import session_factory
from reduct_db.db_dao.paper_dao import PaperDAO
from reduct_db.db_dao.paper_dao import PaperDetailDAO
import datetime

class ReductCard:
    def __init__(self, arXivID: str = "Unknown",
                 info_CN: list[str] = ["Unknown"],
                 info_EN: list[str] = ["Unknown"]):
        # 检索图片的名称
        self.arXivID = arXivID
        # 中文信息
        self.info_CN = info_CN
        # 英文信息
        self.info_EN = info_EN

    def __str__(self):
        return f"[arxivID :{self.arXivID}\nCN :{self.info_CN}\nEN :{self.info_EN}]"

def getCardFromString(text : str) -> ReductCard:
    # print(text)
    lines = text.split("\n")
    id = 13
    while lines[0][id] != '-':
        id += 1
    if lines[0][id - 1] == ' ':
        id -= 1
    arXivID = lines[0][13:int(id)]
    info_CN = splitSentence(lines[1][2:])
    info_EN = splitSentence(lines[-2], False)
    return ReductCard(arXivID = arXivID, info_CN = info_CN, info_EN = info_EN)

def splitSentence(sentence : str, isCN = True):
    res = re.split(r'[，。]', sentence)
    if not isCN:
        res = re.split(r'[,.]', sentence)
    if res[-1] == '':
        res = res[:-1]
    return res

def getCardsFromMarkdown(Path : str) -> list[ReductCard]:
    with open(Path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    resList = []

    # 处理封面
    resList.append(ReductCard(arXivID = 'cover_page', info_CN = splitSentence(lines[0][4:-1])))

    # 植入广告
    # resList.append(ReductCard(arXivID = 'advertise2', info_CN = re.split(r'[，。]',lines[2])[ :-1]))

    ok = False
    curString = ''
    for line in lines:
        if line[0:13] == "## arXiv ID: ":
            ok = True
        elif line[0:13] == "- Meta Info: " :
            ok = False
            if len(curString) > 0:
                resList.append(getCardFromString(curString))
                curString = ""
        if ok:
            curString += line

    # 处理结尾
    resList.append(ReductCard(arXivID='end_page', info_CN = splitSentence("欢迎关注减论，用科技链接个体。")))
    return resList

def getCardsFromReduct_db(guidArray : list[str], total : int) -> list[ReductCard]:
    session = session_factory()
    paper_dao = PaperDAO(session)
    paperDetailDao = PaperDetailDAO(session)
    resList = []
    # todo 封面
    y, m, d = datetime.datetime.today().year, datetime.datetime.today().month, datetime.datetime.today().day
    d = '6'
    coverInfo_CN = f'{y}年{m}月{d}日arXivcs.CV发文量约{total}余篇，减论Agent通过算法为您推荐。在玻尔首页输入感兴趣的论文标题，即可一键开启AI精读，轻松掌握核心内容。'
    resList.append(ReductCard(arXivID = f'{y}-{m}-{d}', info_CN=splitSentence(coverInfo_CN)))

    for guid in guidArray:
        paper = paper_dao.get_by_guid(guid)
        paperDetail = paperDetailDao.get_by_paper_id(paper.id)
        resList.append(ReductCard(arXivID = guid, info_CN = splitSentence(paperDetail.cn_script), info_EN = splitSentence(paperDetail.eng_script, False)))

    # todo 结尾图片
    resList.append(ReductCard(arXivID='end_page', info_CN = splitSentence("欢迎关注减论，用科技链接个体。")))
    return resList