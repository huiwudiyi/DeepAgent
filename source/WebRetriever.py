# coding=utf-8
import json
import hashlib
import time
import urllib.request
import socket


GET_INSTANCE_BY_SERVICE = ''
BNS_NAME = ''
AK = ""
SK = ""
TIMEOUT = 10


def urlRequest(url, headers, body):
    """
    http 请求处理
    @param data 字符串类型
    @param header 请求头
    @param url 地址
    @param timeout 超时时间 
    """
    encode_body = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=encode_body, headers=headers)

    return urllib.request.urlopen(req, timeout=TIMEOUT).read()


def api_auth_sign(params):
    """
    计算Api—Auth
    """
    # Concatenate all strings in the list
    concatenated = ''.join(params)
    
    # Create an MD5 hash of the concatenated string
    md5_hash = hashlib.md5(concatenated.encode('utf-8')).hexdigest()
    
    # Check if the length of the hash is less than 22
    if len(md5_hash) < 22:
        return ""
    
    # Specific indices from which to pick characters from the MD5 hex string
    auth_indices = [7, 3, 17, 13, 1, 21]
    
    # Build the result string using characters at the specified indices
    result = ''
    for idx in auth_indices:
        result += md5_hash[idx]
    
    return result


def requestapi(host, word):
    # 自主开发

    return response

def process_result(response):
    # 自主开发
    return retriever_evidence

def web_retriever(query):
    """
    入口函数
    """
    # 1、线上环境
    apibns = bns.BNS(BNS_NAME)
    host = apibns.get_url() 
    response = requestapi(host, query)
    retriever_evidence = process_result(response)
    return retriever_evidence
#     memory.add_retriever_evidence(memory.query, retriever_evidence)

if __name__ == '__main__':
    print(web_retriever("MoE架构（如Switch Transformer、GPT-4 MoE版本）的具体技术细节、效率提升的量化指标（如训练/推理成本、性能对比）"))

