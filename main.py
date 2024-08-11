from dotenv import load_dotenv
load_dotenv("api_keys.env",override=True)   #override覆盖原来的系统环境变量值

from Tools.Tools import *
from Tools.FileTool import *
from AutoAgent.AutoGPT import *

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_community.vectorstores import FAISS

tools = [
    searchTool,
    calendar_tool,
    calculatorTool,
    websearchTool,
    getCurrentLocationTool,
    getPositionTool,
    getTemperatureTool,
] + file_toolkit.get_tools()

def main():
    llm = ChatOpenAI(model="gpt-4")
    prompts_path = "./Prompts"
    db = FAISS.from_documents([Document(page_content="")],OpenAIEmbeddings(model="text-embedding-ada-002"))
    retriver = db.as_retriever()
    agent = AutoGPT(
        llm=llm,
        prompts_path=prompts_path,
        tools=tools,
        memory_retriver=retriver
    )

    while True:
        task = input("有什么可以帮助您：\n>>>")
        if task.strip().lower() == "quit":
            break
        reply = agent.run(task_description=task,verbose=True)
        print(reply)

if __name__ == '__main__':
    main()
    