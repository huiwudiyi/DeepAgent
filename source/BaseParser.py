class BaseParser:
    """base请求模型"""
    def __init__(self, prompt=None, skill=None, doc='intent'):
        if prompt:
            self.prompt = prompt
        elif skill:
            self.prompt = skill
        else:
            self.prompt = ""
        self.doc = doc
    
    def exceute(self, llm_client, memory) -> dict:
        pass
    
    def gen_prompt(self, memory):
        pass
    
    def parse_result(self, result):
        pass
    
    def vertify(self, result):
        pass

if __name__ == "__main__":
    pass