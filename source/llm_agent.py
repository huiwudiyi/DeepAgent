import requests
import time
import json
from tqdm import *
import pandas as pd
import os
import sys
from requests.exceptions import Timeout
from safety import normalize_json_output

class LLMClient:
    """
    LLM 统一调用封装。

    真实项目中，你可以在这里接入：
    - OpenAI
    - Claude
    - DeepSeek
    - Qwen
    - 本地模型
    """
    def fetch_response(self, url, headers, query_prompt=[]):
        query, doc, prompt = query_prompt
        payload = json.dumps({
            "model": "deepseek",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                },
            ]
        })
        content = {}
        nums = 0 
        while (len(content) == 0 or 'error' in response.text) and nums <= 3:
            time.sleep(3)
            nums += 1
            try:
                response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
                content = response.json()
            except:
                content = {}
        try:
            content = response.json()
        except:
            content = {}
        output_json = {
            "query": query,
            "doc":doc,
            "request_data": content
        }
        return output_json

    def generate_text(self, query: str, doc: str, prompt: str) -> str:
        """
        文本生成接口。
        """
        rqp = [query, doc, prompt]
#         print("rqp", rqp)
        url = ""

        headers = {
            ####自己设置
        }
        result = self.fetch_response(url, headers, rqp)
        content = ""
        try:
            content = result["request_data"]["choices"][0]["message"]["content"]
        except:
            pass
        return content

