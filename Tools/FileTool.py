from langchain_community.agent_toolkits.file_management.toolkit import FileManagementToolkit

#用于和本地文件交互的工具包
file_toolkit = FileManagementToolkit(
    root_dir="./temp"
)