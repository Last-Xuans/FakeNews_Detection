import re
import urllib.parse
from typing import Dict, List, Tuple


class TextAnalyzer:
    """文本分析工具类"""

    @staticmethod
    def extract_domain(url: str) -> str:
        """从URL中提取域名

        Args:
            url: 网址

        Returns:
            域名
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc

            # 去除www前缀
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain
        except Exception:
            return "未知域名"

    @staticmethod
    def count_emotional_words(text: str, emotion_words: List[str] = None) -> int:
        """计算文本中情绪化词汇的数量

        Args:
            text: 要分析的文本
            emotion_words: 情绪化词汇列表，如果为None则使用默认列表

        Returns:
            情绪化词汇数量
        """
        # 默认情绪化词汇列表(简化版)
        if emotion_words is None:
            emotion_words = [
                "震惊", "惊爆", "惊人", "惨烈", "恐怖", "吓人", "吓死", "骇人",
                "不可思议", "犹如噩梦", "不敢相信", "超乎想象", "天价", "绝对",
                "万万没想到", "奇迹", "史上最", "前所未有", "突破天际", "难以置信",
                "疯狂", "崩溃", "狂喜", "不堪入目", "极限", "大批", "全部", "所有",
                "一夜暴富", "爆红", "引爆", "再也无法", "不看后悔", "看完跪了",
                "瞬间", "突然", "秒杀", "独家", "永远", "最终", "必须", "一定"
            ]

        count = 0
        for word in emotion_words:
            count += len(re.findall(word, text))

        return count

    @staticmethod
    def check_grammar_errors(text: str) -> List[str]:
        """简单检查文本中的语法和标点错误

        Args:
            text: 要检查的文本

        Returns:
            错误列表
        """
        errors = []

        # 检查引号配对
        if text.count('"') % 2 != 0:
            errors.append("引号不配对")

        # 检查感叹号或问号过多
        if text.count('!') > 2 or text.count('！') > 2:
            errors.append("感叹号过多")

        if text.count('?') > 2 or text.count('？') > 2:
            errors.append("问号过多")

        # 检查重复标点
        if re.search(r'[,.!?;:]{2,}', text) or re.search(r'[，。！？；：]{2,}', text):
            errors.append("存在重复标点")

        return errors
