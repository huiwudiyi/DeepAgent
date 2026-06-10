from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from BaseParser import BaseParser

class CompleteWriterAgent(BaseParser):
    """文章进一步优化"""

    def __init__(self, prompt=None, skill=None, doc='intent'):
        super().__init__(prompt, skill, doc)
    
    
    def gen_prompt(self, memory):
        draft = memory.get_draft() #???
        if len(draft) < 30:
            return ""
        
        suggestion = memory.get_criticle() #???
        if not isinstance(suggestion, str):
            suggestion = json.dumps(suggestion, ensure_ascii=False)
        
        return self.prompt.replace("{suggest}", suggestion.replace("\n", "")).replace("{初版文稿}", draft)  #???
    
    def parse_result(self, result):
        try:
            result = normalize_json_output(result)
            print("CompleteWriter", result)
            return {
                    "raise_error": [],
                    "content": result
                }
        except:
            return {
                    "raise_error": ["错误原因：模型输出的json结果 格式不正确", "p1"],
                    "content": ""
                }
    def exceute(self, llm_client, memory):
        prompt = self.gen_prompt(memory)
        if len(self.gen_prompt(memory)) == 0:
            raise_error =  ["错误原因：prompt 没有设置", "p0"]
        else:
            for indx in range(3):
                result = llm_client.generate_text(memory.get_query(), self.doc, prompt) 
                if result == "":
                    raise_error = ["错误原因：请求模型出现异常", "p1"]
                    continue
                print("query: ", memory.get_query())
                result = self.parse_result(result)
                raise_error = result["raise_error"]
                if len(raise_error) == 0 and len(result['content']) > 50 and len(result['title']) != 0:
                    memory.set_content(result["content"])
                    return
        return memory.set_raise_error(raise_error)      
        

    