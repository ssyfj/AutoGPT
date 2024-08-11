# 一些小的工具可以统一放在这里，大的单独提成工具文件
# https://q0tozme54s7.feishu.cn/wiki/NFWWwFftIi2jqIkOthncsv4Ankh#Rth1dV6yGoWvUFxxZEac7Jyrn9g
import warnings
warnings.filterwarnings("ignore")   # 忽略警告信息,langchain有些工具会报warning

from ctparse import ctparse
from py_expression_eval import Parser
from langchain_core.pydantic_v1 import BaseModel, Field #注意：这里要写对应的版本，不然会出现各种类别错误，比如：subclass of BaseModel expected (type=type_error.subclass; expected_class=BaseModel)
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import Tool,StructuredTool,tool

from Tools.WebTool import read_webpage
from Tools.MapTool import *
# langchain内置的所有工具---> https://python.langchain.com/v0.2/docs/integrations/tools/

#1.三方API工具，用于搜索
search = SerpAPIWrapper() #搜索引擎
searchTool = Tool.from_function(
        func=search.run,
        name="Search",
        description="用于通过搜索引擎从互联网搜索信息",
    )

#2.日期计算工具
@tool("calendarTool")
def calendar_tool(
        date_exp: str = Field(description="Date expression to be parsed. It must be in English.")
) -> str:
    """用于查询和计算日期/时间"""
    res = ctparse(date_exp)
    date = res.resolution
    return date.dt.strftime("%c")

# 3.计算器工具
def evaluate(expr: str) -> str:
    parser = Parser()
    return str(parser.parse(expr).evaluate({}))

calculatorTool = Tool.from_function(
    func=evaluate,
    name="Calculator",
    description="用于计算一个数学表达式的值",
)

#4.web搜索工具
class WebSearchInput(BaseModel):
    url: str = Field(description="The URL of the web page to search.")
    query: str = Field(description="The query to search.")

websearchTool = StructuredTool.from_function(
    func=read_webpage,
    name="Web Search",
    description="用于从指定的网页中搜索信息",
    args_schema=WebSearchInput,
)

#5.获取当前用户的地址
getCurrentLocationTool = Tool.from_function(
    func=getCurrentLocation,
    name="getCurrentLocation",
    description="用于获取用户当前位置的城市、adcode信息",
)

#6.用于对城市地名、周边设施进行搜索，从而得到地址的详细地址，adcode信息
class positionSearchInput(BaseModel):
    postion: str = Field(description="地址信息，用于定位搜索")
    city: str = Field(description="辅助定位的城市信息,如果没有则默认使用当前用户的位置信息")

getPositionTool = StructuredTool.from_function(
    func=getPostionInfo,
    name="position Search",
    description="对地点进行搜索获取详细地址和adcode信息",
    args_schema=positionSearchInput,
)

#7.根据用户输入的adcode，查询目标区域当前/未来的天气情况
getTemperatureTool = Tool.from_function(
    func=getTemperature,
    name="getTemperature",
    description="根据用户输入的adcode，查询目标区域当前/未来的天气情况",
)
