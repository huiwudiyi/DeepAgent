from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from llm_agent import LLMClient
from BaseParser import BaseParser

class DraftCriticleAgent(BaseParser):
    """查找planner的修改意见"""

    def __init__(self, prompt=None, skill=None, doc='intent'):
        super().__init__(prompt, skill, doc)
    
    def gen_prompt(self, memory):
        brief = memory.get_brief()
        main_goal = brief.get("main_goal", "")
        if len(main_goal) < 20:
            return ""
        success_criteria = brief.get("success_criteria", "")
        if len(success_criteria) == 0:
            return ""
        if not isinstance(success_criteria, str):
            success_criteria = json.dumps(success_criteria, ensure_ascii=False)
        draft = memory.get_draft() # ???
        if len(draft) < 30:
            return ""
        return self.prompt.replace("{query}", memory.get_query()).replace("{main_goal}", main_goal).replace("{验收条件}", success_criteria).replace("{初版文稿}", draft)
    
    def parse_result(self, result):
        try:
            result = normalize_json_output(result)
            print("DraftCriticle", result)
            is_complete = result["is_complete"]
            need_fix = result["need_fix"]
            fix_suggestion = result["fix_suggestion"]
            return {
                    "raise_error": [],
                    "is_complete": is_complete,
                    "need_fix": need_fix,
                    "fix_suggestion": fix_suggestion
                }
        except:
            return {
                    "raise_error": ["错误原因：模型输出的json结果 格式不正确", "p1"],
                    "is_complete": "",
                    "need_fix": "",
                    "fix_suggestion": ""
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
                is_complete = result["is_complete"]
                need_fix = result["need_fix"]
                fix_suggestion = result["fix_suggestion"]
                if len(raise_error) == 0 or need_fix == "must":
                    memory.set_criticle(fix_suggestion.replace("\n","")) # ???
                    return
                if need_fix in ["optinal", "no"]:
                    return 
        return memory.set_raise_error(raise_error)


    