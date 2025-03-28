import time
import json
import requests
from typing import Dict, Any
import sys
import os

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import LLM_API_CONFIG

class LLMConnector:
    """大模型API连接器"""
    
    def __init__(self, api_config: Dict[str, Any] = None):
        """初始化连接器
        
        Args:
            api_config: API配置，默认使用config.py中的配置
        """
        self.api_config = api_config or LLM_API_CONFIG
    
    def get_response(self, prompt: str) -> str:
        """调用大模型API获取回复
        
        Args:
            prompt: 提示词
            
        Returns:
            模型回复文本
        """
        # 通义千问API
        if "dashscope.aliyuncs.com" in self.api_config["API_URL"]:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_config['API_KEY']}"
            }
            
            payload = {
                "model": self.api_config["MODEL"],
                "input": {
                    "messages": [{"role": "user", "content": prompt}]
                },
                "parameters": {
                    "temperature": self.api_config["TEMPERATURE"],
                    "max_tokens": self.api_config["MAX_TOKENS"]
                }
            }
            
            response = requests.post(
                self.api_config["API_URL"],
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"API调用失败: {response.text}")
                
            result = response.json()
            return result["output"]["text"]
        
        # 通用格式(OpenAI接口)
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_config['API_KEY']}"
            }
            
            payload = {
                "model": self.api_config["MODEL"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.api_config["TEMPERATURE"],
                "max_tokens": self.api_config["MAX_TOKENS"]
            }
            
            response = requests.post(
                self.api_config["API_URL"],
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"API调用失败: {response.text}")
                
            result = response.json()
            return result["choices"][0]["message"]["content"]
