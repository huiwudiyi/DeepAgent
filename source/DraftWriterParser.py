from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from llm_agent import LLMClient
from BaseParser import BaseParser

class DraftWriterParser(BaseParser):
    """Draft 初版书写"""

    def __init__(self, prompt=None, skill=None, doc='intent'):
        super().__init__(prompt, skill, doc)
    
    def gen_prompt(self, memory):
        outline_str = ""
        outline = memory.outline #???
        evendence_dict = memory.retriever_evidence #??
        indx = 1
        for section in outline:
            idx = section["id"]
            sub_goal = section["sub_goal"]
            key_points = section["key_points"]
            outline_str += "\n\nparagraph " + str(indx) + ":\n" + "  目标：" + sub_goal + "\n  书写过程：\n" + "    -"+ "\n    -".join(key_points) 
            if idx in evendence_dict.keys():
                outline_str += "\n  辅助材料：\n" + "    -"+ "\n    -".join(evendence_dict[idx]) + "\n"
            indx += 1
        return self.prompt + outline_str + "\n\n按照上面的创作流程创作内容，paragraph使用不同的标题级别。一级标题（如“一、”）、二级标题（如“1.1”）通常不出现四级标题 ， 并且以markdown格式开始输出正文"
    
    def parse_result(self, result):
        print("draft", result)
        if len(result) > 30:
            return {
                    "raise_error": [],
                    "draft": result
            }
        else:
            return {
                    "raise_error": ["错误原因：模型输出的json结果 格式不正确", "p1"],
                    "draft": "",
                }
    def exceute(self, llm_client, memory):
        raise_error = []
        prompt = self.gen_prompt(memory)
        if len(self.gen_prompt(memory)) == 0:
            raise_error =  ["错误原因：prompt 没有设置", "p0"]
        else:
            for indx in range(3):
                print("执行轮数", indx)
                result = llm_client.generate_text(memory.get_query(), self.doc, prompt) 
                raise_error = ""
                if result == "":
                    raise_error = ["错误原因：请求模型出现异常", "p1"]
                    continue
                result = self.parse_result(result)
                raise_error = result["raise_error"]
                if len(raise_error) == 0:
                    memory.draft = result['draft'] #???
                    return
        return memory.set_raise_error(raise_error)            

    