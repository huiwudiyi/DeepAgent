from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from BaseParser import BaseParser

class RewriteQueryAgent(BaseParser):
    """rewrite query生成"""

    def __init__(self, prompt=None, skill=None, doc='rewrite'):
        super().__init__(prompt, skill, doc)
    
    def gen_prompt(self, memory):
        if len(memory.get_query().strip()) == 0:
            self.prompt = ""
            return ""
        return self.prompt + memory.get_query()

    def parse_result(self, result):
        try:
            result = normalize_json_output(result)
            print("RewriteQueryAgent", result)
            need_search = result["need_search"]
            search_query = result["search_query"]
            return {
                    "raise_error": [],
                    "need_search": need_search,
                    "search_query": search_query,
            }
        except:
            return {
                    "raise_error": ["错误原因：模型输出的json结果 格式不正确", "p1"],
                    "need_search": "",
                    "search_query": "",
                }

    def exceute(self, llm_client, memory):
        raise_error = []
        prompt = self.gen_prompt(memory)
        if len(self.gen_prompt(memory)) == 0:
            raise_error =  ["错误原因：prompt 没有设置", "p0"]
        else:
            for indx in range(3):
                result = llm_client.generate_text(memory.get_query(), self.doc, prompt) 
                raise_error = ""
                if result == "":
                    raise_error = ["错误原因：请求模型出现异常", "p1"]
                    continue
                print("query: ", memory.get_query())
                result = self.parse_result(result)
                raise_error = result["raise_error"]
                if len(raise_error) == 0:
                    memory.set_need_search(result["need_search"])
                    memory.set_search_query(result["search_query"])
                    return
        return memory.set_raise_error(raise_error)
        
