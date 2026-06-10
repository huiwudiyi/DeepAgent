from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from BaseParser import BaseParser

class IntentAgent(BaseParser):
    """意图识别"""

    def __init__(self, prompt=None, skill=None, doc='intent'):
        super().__init__(prompt, skill, doc)
    
    def gen_prompt(self, memory):
        if len(memory.get_query().strip()) == 0:
            self.prompt = ""
            return ""
        return self.prompt + memory.get_query()

    def parse_result(self, result):
        try:
            result = normalize_json_output(result)
            print("IntentAgent", result)
            intent = result["intent"]
            number = result["number"]
            time = result["time"]
            sub_intent = result["sub_intent"]
            holiday = result["holiday"]
            return {
                    "raise_error": [],
                    "intent": intent,
                    "sub_intent": sub_intent,
                    "number": number,
                    "time": time,
                    "holiday": holiday
            }
        except:
            return {
                    "raise_error": ["错误原因：模型输出的json结果 格式不正确", "p1"],
                    "intent": "",
                    "sub_intent" : "",
                    "number": "",
                    "time": "",
                    "holiday": ""
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
                    memory.set_intent(result["intent"])
                    memory.set_sub_intent(result["sub_intent"])
                    memory.set_time(result["time"])
                    memory.set_number(result["number"])
                    memory.set_holiday(result["holiday"])
                    return
        return memory.set_raise_error(raise_error)
        
