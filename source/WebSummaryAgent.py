from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List
from safety import normalize_json_output
from llm_agent import LLMClient
from WebRetriever import web_retriever
from BaseParser import BaseParser

class WebSummaryAgent(BaseParser):
    """检索内容总结"""

    def __init__(self, prompt=None, skill=None, doc='intent'):
        super().__init__(prompt, skill, doc)

    def gen_prompt(self, query):
        evidence = web_retriever(query)
        if len(query.strip()) == 0 or len(evidence) == 0:
            self.prompt = ""
            return ""
        return self.prompt.replace("{question}", query).replace("{chunks}", json.dumps(evidence, ensure_ascii=False))

    def parse_result(self, result):
        try:
            result = normalize_json_output(result)
            print("result", result)
            result = result.get("final_answer", {})
            can_answer = result.get("can_answer", "")
            confidence = result.get("confidence", "")
            answer = result.get("answer", "")
            return {
                    "raise_error": "",
                    "can_answer": can_answer,
                    "confidence": confidence,
                    "answer": answer
                }
        except:
            return {
                    "raise_error": ["错误原因：模型输出的json结果 格式不正确", "p1"],
                    "can_answer": "",
                    "confidence": "",
                    "answer": ""
                }
    def exceute(self, llm_client, memory, ids, query):
        raise_error = []
        prompt = self.gen_prompt(query)
        if len(self.gen_prompt(query)) == 0:
            raise_error =  ["错误原因：prompt 没有设置", "p0"]
            print("raise_error", raise_error)
        else:
            for indx in range(3):
                print("执行轮数", indx)
                result = llm_client.generate_text(query, self.doc, prompt) 
                raise_error = ""
                if result == "":
                    raise_error = ["错误原因：请求模型出现异常", "p1"]
                    continue
                result = self.parse_result(result)
                raise_error = result["raise_error"]
                can_answer = result["can_answer"]
                confidence = result["confidence"]
                answer = result["answer"]
                if can_answer.strip() == "否":
                    return 
                if can_answer =="是" and confidence in ["low"]:
                    return
                if len(raise_error) == 0 and can_answer =="是" and confidence in ["high", "medium"]:
                    memory.add_retriever_evidence(ids, answer.replace("\n", ""))
                    return
        return memory.set_raise_error(raise_error)               
    
