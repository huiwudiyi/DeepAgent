from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from BaseParser import BaseParser

class RagAgent(BaseParser):
    """将用户的query RagParser"""

    def __init__(self, prompt=None, skill=None, doc='rag'):
        super().__init__(prompt, skill, doc)
    
    def gen_prompt(self, memory):
        if len(memory.query.strip()) == 0:
            self.prompt = ""
            return ""
        return self.prompt.replace("{query}", memory.query).replace("{rag_result}", memory.evdences)

    def parse_result(self, result):
        try:
            result = normalize_json_output(result)
            all_result = []
            for res in result:
                confidence = res["confidence"]
                if confidence == "high":
                    all_result.append(res["result"])
            return {
                    "raise_error": [],
                    "result": all_result,
                    }
        except:
            return {
                    "raise_error": ["错误原因：模型输出的json结果 格式不正确", "p1"],
                    "result": "",
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
                print("za_result", result)
                result = self.parse_result(result)
                raise_error = result["raise_error"]
                if len(raise_error) == 0:
                    memory.writer_content = result["result"]
                    return
        return memory.set_raise_error(raise_error)