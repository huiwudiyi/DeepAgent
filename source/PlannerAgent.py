from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from BaseParser import BaseParser

class PlannerAgent(BaseParser):
    """将用户的query 详细的拆成brief"""

    def __init__(self, prompt=None, skill=None, doc='intent'):
        super().__init__(prompt, skill, doc)
    
    def gen_prompt(self, memory):
        brief = memory.get_brief()
        if "raise_error" in brief.keys():
            raise_error = brief["raise_error"]
            if len(raise_error) != 0:
                del brief["raise_error"]
                return ""
        if len(memory.get_query().strip()) == 0 or len(brief) < 3:
            self.prompt = ""
            return ""
        return self.prompt.replace("{query}", memory.get_query()).replace("{约束条件}", json.dumps(brief, ensure_ascii=False, indent=2))
    
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
                print("query: ", memory.get_query())
                result = self.parse_result(result)
                raise_error = result["raise_error"]
                if len(raise_error) == 0:
                    memory.set_sections(result["sections"])
                    return
        return memory.set_raise_error(raise_error)
    
