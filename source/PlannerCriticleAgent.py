from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from BaseParser import BaseParser

class PlannerCriticleAgent(BaseParser):
    """查找planner的修改意见"""

    def __init__(self, prompt=None, skill=None, doc='intent'):
        super().__init__(prompt, skill, doc)
    
    def gen_prompt(self, memory):
        if len(memory.get_query().strip()) == 0:
            self.prompt = ""
            return ""
        brief = memory.get_brief()
        if "raise_error" in brief.keys():
            raise_error = brief["raise_error"]
            if len(raise_error) != 0:
                self.prompt = ""
                return ""
            else:
                del brief["raise_error"]
        outlines = memory.get_sections()
        if len(outlines) <= 1:
            self.prompt = ""
            return ""
        # json.dumps(outline, ensure_ascii=False, indent=2)
        return self.prompt.replace("{query}", memory.get_query()).replace("{约束条件}", json.dumps(brief, ensure_ascii=False, indent=2)).replace("{outline}", json.dumps(outlines, ensure_ascii=False, indent=2))
    
    def parse_result(self, result):
        try:
            result = normalize_json_output(result)
            print("plannerCriticle", result)
            is_complete = result["is_complete"]
            issues = result["issues"]
            return {
                    "raise_error": [],
                    "is_complete": is_complete,
                    "issues": issues
                }
        except:
            return {
                    "raise_error": ["错误原因：模型输出的json结果 格式不正确", "p1"],
                    "issues": [],
                    "is_complete": ""
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
                    memory.set_issues(result["issues"])
                    return
        return memory.set_raise_error(raise_error)
