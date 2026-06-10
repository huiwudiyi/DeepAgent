from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from llm_agent import LLMClient
from BaseParser import BaseParser

class PlannerSearchQueryParser(BaseParser):
    """将outline中 添加rag query"""

    def __init__(self, prompt=None, skill=None, doc='intent'):
        super().__init__(prompt, skill, doc)
    
    def gen_prompt(self, memory):
        main_goal = memory.brief["main_goal"]
        if len(main_goal.strip()) == 0:
            self.prompt = ""
            return ""
        outline = memory.outline
        if len(outline) == 0:
            return ""
        return self.prompt.replace("{main_goal}", main_goal).replace("{outline}", json.dumps(outline, ensure_ascii=False, indent=2))

    def parse_result(self, result):
        try:
            result = normalize_json_output(result)
            print("search_query", result)
            sections = result["sections"]
            return {
                    "raise_error": [],
                    "sections": sections
                }

        except:
            return {
                    "raise_error": ["错误原因：模型输出的json结果 格式不正确", "p1"],
                    "sections": ""
                }
                    
    def exceute(self, llm_client, memory):
        raise_error = []
        prompt = self.gen_prompt(memory)
        if len(self.gen_prompt(memory)) == 0:
            raise_error =  ["错误原因：prompt 没有设置", "p0"]
        else:
            for indx in range(3):
                print("执行轮数", indx)
                result = llm_client.generate_text(memory.query, self.doc, prompt) 
                raise_error = ""
                if result == "":
                    raise_error = ["错误原因：请求模型出现异常", "p1"]
                    continue
                result = self.parse_result(result)
                raise_error = result["raise_error"]
                if len(raise_error) == 0:
                    memory.set_search_query(result["sections"])
                    return
        return memory.set_raise_error(raise_error)



    