from langchain_core.language_models import BaseChatModel,BaseLLM
from langchain_core.tools import BaseTool
from langchain.vectorstores.base import VectorStoreRetriever    # 向量库检索
from langchain.output_parsers import PydanticOutputParser,OutputFixingParser
from typing import List, Optional
from Utils.ThoughtAndAction import *
from Utils.CommonUtils import *
from Utils.PromptTemplateBuilder import PromptTemplateBuilder
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.pydantic_v1 import ValidationError
from langchain.memory import ConversationSummaryMemory,VectorStoreRetrieverMemory   # 向量库检索记忆
from langchain_openai import OpenAI

class AutoGPT:
    def __init__(
        self,
        llm: BaseLLM | BaseChatModel,   #取一个
        prompts_path: str,
        tools: List[BaseTool],
        agent_name: Optional[str] = "哈哈",
        agent_role: Optional[str] = "智能助手机器人,可以通过使用工具与指令自动化解决问题",
        max_thought_steps: Optional[int] = 10,  #最长思考步数（短时记忆）
        memory_retriver: Optional[VectorStoreRetriever] = None  #用于长时记忆,向量库检索
    ):
        self.llm = llm
        self.prompts_path = prompts_path
        self.tools = tools
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.max_thought_steps = max_thought_steps
        self.memory_retriver = memory_retriver
        
        self.output_parser = PydanticOutputParser(   
            pydantic_object=ThoughtAndAction
        )
        
        self.step_prompt = PromptTemplateBuilder(self.prompts_path,"step_instruction.templ").build().format()
        self.force_rethink_prompt = PromptTemplateBuilder(self.prompts_path,"force_rethink.templ").build().format()
        
    def run(self,task_description:str,verbose=False)->str:
        thought_step_count = 0  #当前思考轮数
        
        #构造promptTemplate，还差长短时记忆和step_instruction的处理(后面逻辑实现)
        prompt_template = PromptTemplateBuilder(
            self.prompts_path,
        ).build(
            tools=self.tools,
            output_parser=self.output_parser
        ).partial(
            ai_name=self.agent_name,
            ai_role=self.agent_role,
            task_description=task_description,
        )
        chain = prompt_template | self.llm
        
        short_term_memory = ConversationBufferWindowMemory(
            ai_prefix="Reason", #默认格式是：human和AI，AutoGpt不存在human，所以改成和我们情况符合的思考和行动
            human_prefix="Act",
            k=self.max_thought_steps,   # 短时记忆存储的窗口大小，设置为思考步数，表示全部存储
        )
        
        # 长时记忆通过summary来总结
        summary_memory = ConversationSummaryMemory(
            llm=OpenAI(temperature=0),    #default gpt-3.5-turbo-instruct  temperature减少随机性，0减少随机但是不代表不随机
            buffer="问题："+task_description+"\n",  
            ai_prefix="Reason",
            human_prefix="Act",
        )
        
        if self.memory_retriver is not None:
            long_term_memory = VectorStoreRetrieverMemory(  # 从向量库检索器中获取长时记忆,如果和之前的任务相关，就可以从向量库中检索到，作为长时记忆放入promptTemplate中
                retriever=self.memory_retriver,
            )
        else:
            long_term_memory = None
        
        last_action = None  #更新上一次的action标识
        finish_turn = False #是否完成任务，判断action是否是FINISH得到，如果完成，需要进行输出最终结果
        while thought_step_count < self.max_thought_steps:
            # 调用一次step，获取thought和action
            thought_and_action = self._step(    
                chain=chain,
                task_description=task_description,
                short_term_memory=short_term_memory,
                long_term_memory=long_term_memory,
            )
            # 判断是否重复，如果重复，则需要重新思考
            action = thought_and_action.action
            if self._is_repeated(last_action,action):   #这里只让他进行一次重思考
                thought_and_action = self._step(
                    chain=chain,
                    task_description=task_description,
                    short_term_memory=short_term_memory,
                    long_term_memory=long_term_memory,
                    force_rethink=True,
                )
                action = thought_and_action.action  
            
            # 更新上一次的action
            last_action = action
            
            # 打印当前的thought和action
            if verbose:
                print(thought_and_action.thought.format())
                
            # 根据指令判断整体任务是否完成
            if thought_and_action.is_finish():  # 之所以在这里判断finish进行break，因为是根据前面的short_term_memory来判断的任务结束，所以不需要存储后面的short_term_memory,任务已经结束
                finish_turn = True  
                break
            
            # 正常情况下，是需要去调用工具
            tool = self._find_tool(action.name)
            if tool is None: #没有找到对应的工具，报错
                result = (
                    f"Error: 找不到工具或指令 '{action.name}'. "
                    f"请从提供的工具/指令列表中选择，请确保按对的格式输出."
                )
            else:   #找到工具，进行运行，得到结果
                try:
                    observation = tool.run(action.args)
                except ValidationError as e:
                    observation = (
                        f"Validation Error in args: {str(e)}, args: {action.args}."
                    )
                except Exception as e:
                    observation = (
                        f"Error: {str(e)}, {type(e).__name__}, args: {action.args}."
                    )
                result = (
                    f"执行：{action.format()}\n"
                    f"返回结果：{observation}"
                )
            # 打印中间结果
            if verbose:
                print(result)
                
            # 更新短时记忆，存储thought和action作为输入,以及执行结果作为输出
            short_term_memory.save_context(
                {"input":thought_and_action.thought.format()},
                {"output":result}
            )
            
            # 更新短时记忆时，也更新一下长时记忆，但是长时记忆是通过summary来总结
            summary_memory.save_context(
                {"input":thought_and_action.thought.format()},
                {"output":result}
            )
            
            thought_step_count += 1
            
        # 任务结束的时候，加入长时记忆即可
        if long_term_memory is not None:
            long_term_memory.save_context(
                {"input":task_description},
                {"output":summary_memory.load_memory_variables({})["history"]}
            )

        reply = ""
        if finish_turn: # 如果满足结束条件，则返回结果
            reply = self._final_step(short_term_memory,task_description)
        else:   #没有结果，返回最后一次思考的结果
            reply = thought_and_action.thought.speak
        
        return reply
        
    def _step(self,chain,task_description,short_term_memory,long_term_memory,force_rethink=False):
        #去向量库里检索相似度符合的长时记忆
        longMemoty = ""
        if long_term_memory is None:
            longMemoty = long_term_memory.load_memory_variables({
                "prompt":task_description, #拿任务检索内存memory，获取历史记录；至于里面的key，并不重要，可以认为是标识而已；根据相似度检索的
            })["history"]
            
        current_response = chain.invoke({
            "short_term_memory": short_term_memory.load_memory_variables({})["history"],
            "long_term_memory":longMemoty,
            "step_instruction":self.step_prompt if not force_rethink else self.force_rethink_prompt,
        })
        try:
            thought_and_action = self.output_parser.parse(ChinsesFriendly(current_response.content))
        except Exception as e:
            print("---------------------------------------------------")
            print(ChinsesFriendly(current_response.content))    #这个地方容易报错，暂时没有查出来，偶尔报错
            print("---------------------------------------------------")
        return thought_and_action
    
    #用于判断两次action(Action对象)是否重复，如果重复需要reforce，判断名称和参数
    def _is_repeated(self,last_action,action):
        #判断obj
        if last_action is None:
            return False
        if action is None:
            return True
        
        #判断name
        if last_action.name != action.name:
            return False
        
        #判断参数
        if set(last_action.args.keys()) != set(action.args.keys()):
            return False
        
        for k,v in last_action.args.items():
            if action.args[k] != v:
                return False
            
        return True

    #根据名称查找工具
    def _find_tool(self,tool_name):
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def _final_step(self,short_term_memory,task_description):
        finish_prompt = PromptTemplateBuilder(self.prompts_path,"finish_instruction.templ").build().partial(
            ai_name = self.agent_name,
            ai_role = self.agent_role,
            task_description = task_description,
            short_term_memory = short_term_memory.load_memory_variables({})["history"],
        )
        
        chain = finish_prompt | self.llm
        response = chain.invoke({})
        return response