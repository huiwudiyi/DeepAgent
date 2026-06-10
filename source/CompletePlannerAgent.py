from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from llm_agent import LLMClient
from BaseParser import BaseParser

class CompletePlannerAgent(BaseParser):
    """planner进行优化"""

    def __init__(self, prompt=None, skill=None, doc='intent'):
        super().__init__(prompt, skill, doc)
    
    def process_suggest(self, suggest_info):
        suffest_str = []
        for issue in suggest_info:
            need_fix = issue["need_fix"]
            type_str = issue["type"]
            if need_fix == "是":
                suffest_str.append(issue["fix_suggestion"].replace("\n", ""))
        return "\n".join(suffest_str)
    
    def gen_prompt(self, memory):
        suggest_info = self.process_suggest(memory.get_issues())
        if len(suggest_info.strip()) < 30:
            self.prompt = ""
            return ""
        outline = json.dumps(memory.get_sections(), ensure_ascii=False, indent=2)
        if len(outline) < 30:
            self.prompt = ""
            return ""
        return self.prompt.replace("{query}", memory.get_query()).replace("{outline}", outline).replace("{suggest}", suggest_info)   
    
    def parse_result(self, result):
        try:
            result = normalize_json_output(result)
            print("planner", result)
            title = result["title"]
            sections = result["sections"]
            return {
                    "raise_error": [],
                    "title": title,
                    "sections": sections
                }

        except:
            return {
                    "raise_error": ["错误原因：模型输出的json结果 格式不正确", "p1"],
                    "title": "",
                    "sections": ""
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
                print("query", memory.get_query())
                result = self.parse_result(result)
                raise_error = result["raise_error"]
                if len(raise_error) == 0:
                    memory.set_outlines(result["sections"])
                    return
        return memory.set_raise_error(raise_error)

