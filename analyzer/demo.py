from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.tools import Tool

from deprecated_code.agent_tools.arxiv_tools import gs_cite_tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from crawler.gs_author_crawler import find_author
llm_model = "moonshot-v1-8k"
from langchain.chat_models import ChatOpenAI
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

chain = prompt | ChatOpenAI()

chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: SQLChatMessageHistory(
        session_id=session_id, connection_string="mysql+mysqlconnector://root:1q2w3e4r5t@localhost/dailypaper"
    ),
    input_messages_key="question",
    history_messages_key="history",
)
config = {"configurable": {"session_id": "test0002"}}
tools_appendix = [
    Tool(
        name="find_author",
        func=find_author,
        description="useful for when you need to know the information of a certain author."
    ),
    Tool(
        name="get_cites",
        func=gs_cite_tool,
        description="useful for when you need to know one's citation counts."
    ),
]



llm = ChatOpenAI(temperature=0, model=llm_model)
# tools = load_tools(["llm-math"], llm=llm)

agent = initialize_agent(
    tools_appendix,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,
)
while True:
    user_input = input("> ")
    response = chain_with_history.invoke({"question": user_input}, config=config)
    # response = agent.run(user_input)
    print(f'Assistant: {response.content}')