import sys
import os
from typing import Dict, Any

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models.llm_connector import LLMConnector
from src.rules.detection_rules import get_combined_prompt
from src.utils.text_analyzer import TextAnalyzer
from src.utils.result_parser import ResultParser
from config import THRESHOLDS


class FakeNewsDetector:
    """虚假新闻检测核心类"""

    def __init__(self):
        """初始化检测器"""
        self.llm = LLMConnector()
        self.text_analyzer = TextAnalyzer()
        self.result_parser = ResultParser()

    def preprocess_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """预处理新闻数据

        Args:
            news_data: 原始新闻数据

        Returns:
            预处理后的新闻数据
        """
        processed_data = news_data.copy()

        # 提取域名（如果有URL）
        if "url" in news_data and news_data["url"]:
            processed_data["domain"] = self.text_analyzer.extract_domain(news_data["url"])
        elif "domain" not in news_data or not news_data["domain"]:
            processed_data["domain"] = "未知来源"

        return processed_data

    def detect(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行虚假新闻检测

        Args:
            news_data: 新闻数据，必须包含title和content字段

        Returns:
            检测结果
        """
        # 参数校验
        if not news_data.get("title") or not news_data.get("content"):
            raise ValueError("新闻数据必须包含标题(title)和内容(content)")

        # 预处理数据
        processed_data = self.preprocess_news(news_data)

        # 构建提示词
        prompt = get_combined_prompt(processed_data)

        # 调用大模型
        response = self.llm.get_response(prompt)

        # 解析结果
        result = self.result_parser.parse_model_response(response)

        # 添加风险级别评估
        risk_percentage = result["conclusion"]["risk_percentage"]
        if risk_percentage >= THRESHOLDS["HIGH_RISK_THRESHOLD"]:
            result["risk_level"] = "高风险"
        elif risk_percentage <= THRESHOLDS["LOW_RISK_THRESHOLD"]:
            result["risk_level"] = "低风险"
        else:
            result["risk_level"] = "中等风险"

        return result
