import re
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResultParser:
    """解析大模型返回结果"""

    @staticmethod
    def parse_model_response(response: str) -> Dict[str, Any]:
        """解析模型响应，提取结构化结果

        Args:
            response: 大模型的回复文本

        Returns:
            结构化的分析结果
        """
        result = {
            "rules": {},
            "conclusion": {
                "risk_percentage": 0,
                "explanation": ""
            }
        }

        # 记录原始响应以便调试
        logger.info(f"解析模型响应: {response[:200]}...")

        # 解析每条规则结果
        for i in range(1, 7):
            rule_pattern = rf"规则{i}:\s*\[([^\]]+)\]\s*-\s*(.+?)(?=规则|综合|$)"
            rule_match = re.search(rule_pattern, response, re.DOTALL)

            if rule_match:
                verdict = rule_match.group(1).strip()
                reason = rule_match.group(2).strip()
                
                logger.info(f"规则{i}原始判断: {verdict}")

                # 统一表示方式：当判断包含关键词时表示有风险
                if verdict.lower() in ["符合", "是", "存在", "有"]:
                    standardized_verdict = "符合"  # 符合表示有风险
                else:
                    standardized_verdict = "不符合"  # 不符合表示无风险
                
                logger.info(f"规则{i}标准化判断: {standardized_verdict}")

                result["rules"][f"rule{i}"] = {
                    "verdict": standardized_verdict,
                    "reason": reason
                }
            else:
                # 如果匹配失败，设置默认值
                logger.warning(f"规则{i}匹配失败")
                result["rules"][f"rule{i}"] = {
                    "verdict": "未知",
                    "reason": "模型未给出明确结论"
                }

        # 解析综合结论
        conclusion_pattern = r"综合结论:\s*\[?(\d+)%?\]?\s*[可能性为]*虚假新闻\s*-\s*(.+)"
        conclusion_match = re.search(conclusion_pattern, response, re.DOTALL)

        if conclusion_match:
            try:
                risk_percentage = int(conclusion_match.group(1))
                explanation = conclusion_match.group(2).strip()
                logger.info(f"找到风险百分比: {risk_percentage}%")
                result["conclusion"]["risk_percentage"] = risk_percentage
                result["conclusion"]["explanation"] = explanation
            except (ValueError, IndexError) as e:
                logger.error(f"解析风险百分比失败: {e}")
                result["conclusion"]["explanation"] = "无法解析风险百分比，请查看原始响应"
        else:
            logger.warning("未找到风险百分比，从规则结果推断")
            # 如果没有找到明确的百分比，尝试从规则结果推断
            risk_score = 0
            risk_rules_count = 0

            for rule_key, rule_data in result["rules"].items():
                if rule_data["verdict"] == "符合":
                    risk_rules_count += 1

            # 根据符合规则数量估算风险
            if risk_rules_count > 0:
                risk_score = min(100, risk_rules_count * 17)  # 每条约17%，6条约100%
            
            logger.info(f"推断风险百分比: {risk_score}% (基于{risk_rules_count}条风险规则)")
            result["conclusion"]["risk_percentage"] = risk_score
            result["conclusion"]["explanation"] = f"基于{risk_rules_count}条风险规则推断"

        # 添加原始响应以便参考
        result["raw_response"] = response

        return result
