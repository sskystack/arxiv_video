"""
内容生成模块
"""
import os
import arxiv
from openai import OpenAI

def get_paper_details(paper_id):
    """
    使用 arxiv anaconda_lib 根据论文ID获取论文的详细信息。

    :param paper_id: ArXiv 论文ID (例如: "2308.04152")。
    :return: 包含论文标题和摘要的字典，如果找不到则返回 None。
    """
    print(f"🔍 正在从 ArXiv API 获取论文 {paper_id} 的详细信息...")
    try:
        # 使用 arxiv anaconda_lib 搜索论文
        search = arxiv.Search(id_list=[paper_id])
        paper = next(search.results())
        
        if paper:
            details = {
                "title": paper.title,
                "summary": paper.summary
            }
            print(f"✅ 成功获取论文标题: 《{paper.title}》")
            return details
        else:
            print(f"❌ 未能找到论文 {paper_id} 的信息。")
            return None
    except Exception as e:
        print(f"获取论文 {paper_id} 信息时出错: {e}")
        return None

def generate_commentary(paper_details):
    """
    根据论文信息，使用 OpenAI 语言模型生成视频解说词。

    :param paper_details: 包含论文标题和摘要的字典。
    :return: 生成的解说词文本，如果失败则返回 None。
    """
    if not paper_details:
        return None

    print(f"🤖 正在为论文《{paper_details.get('title', '未知标题')}》生成解说词...")

    try:
        # --- 安全地获取 API 密钥 ---
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ 错误: OPENAI_API_KEY 环境变量未设置。")
            print("请设置该环境变量以使用 OpenAI API。")
            return None
        
        client = OpenAI(api_key=api_key)

        # --- 构建 Prompt ---
        prompt = f"""
        你是一个顶级的科研讲解员，擅长将复杂论文的核心思想转化为通俗易懂、引人入胜的中文视频解说词。
        请根据以下论文信息，为我生成一段大约300字的视频解说词。

        要求:
        1. 开头需要简洁地介绍这篇论文的标题和核心贡献。
        2. 中间部分要生动地讲解论文的关键方法和实现效果，可以结合视频画面进行想象。
        3. 结尾要总结论文的意义或对未来的展望。
        4. 语言风格要专业、流畅，同时易于理解。

        论文标题: {paper_details['title']}

        论文摘要:
        {paper_details['summary']}
        """

        # --- 调用 OpenAI API ---
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 你也可以选择 gpt-4 或其他模型
            messages=[
                {"role": "system", "content": "你是一个顶级的科研讲解员。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        script = response.choices[0].message.content.strip()
        print("✅ 解说词生成完毕。")
        return script

    except Exception as e:
        print(f"调用 OpenAI API 时出错: {e}")
        return None
