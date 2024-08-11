from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Optional,List,Dict,Any

class Action(BaseModel):
   name: str = Field(description="工具或指令名称")
   args: Optional[Dict[str, Any]] = Field(description="工具或指令参数，由参数名称和参数值组成")

   def format(self) -> str:
      ans = f"{self.name}("
      if self.args is None or len(self.args) == 0:
         ans += ")"
      for k,v in self.args.items():
         ans += f"{k}={v},"
      ans = ans[:-1] + ")"
      return ans

class Thought(BaseModel):
   text: str = Field(description="思考内容")
   reasoning: str = Field(description="思考过程")
   plan: List[str] = Field(description="思考结果形成一系列的执行计划")  #一系列，指的是？
   criticism: str = Field(description="constructive self-criticism,思考过程中的自我反思")   #反思机制，思考上面思考过程是否有可以完善的地方。如果本轮不工作，可以为下一轮提供帮助。和思维链相似
   speak:str = Field(description="将思考结果转换为语言，用于输出")  #类似输出，用语言叙述出来要做的事情---->这个叙述后面会被转成action（类似思维链的一个过程）
   
   def format(self) -> str:
      def format_plans(plans: List[str]) -> str:
         ans = ""
         for plan in plans:
            ans += f"- {plan}\n"
         return ans.strip()
      ans = (
         "\n"
         f"思考：{self.text}\n"
         f"推理：{self.reasoning}\n"
         f"计划：{format_plans(self.plan)}\n"
         f"反思：{self.criticism}\n"
         f"输出：{self.speak}\n"
         "\n"
      )
      return ans
      
class ThoughtAndAction(BaseModel):
    thought: Thought = Field(description="思考过程")
    action: Action = Field(description="当前的执行动作")
    
    def is_finish(self)->bool:
        return self.action.name.lower() == "finish"
            