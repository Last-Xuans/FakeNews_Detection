from typing import List, Dict, Any

# 定义新闻检测规则
DETECTION_RULES = [
    {
        "id": "rule1",
        "name": "域名可信度检查",
        "description": "新闻来自一个不知名或需要怀疑的域名URL。",
        "prompt_template": "首先分析新闻来源网站域名'{domain}'的可信度。是否是知名媒体网站？该域名是否可疑？",
        "weight": 0.2  # 规则权重
    },
    {
        "id": "rule2",
        "name": "标题情绪化检查",
        "description": "新闻标题中是否包含耸人听闻的引子、挑衅性或情绪化的语言、或夸张的声明，新闻可能是假的。",
        "prompt_template": "分析新闻标题'{title}'中是否包含耸人听闻的词语、挑衅性或情绪化的语言、或夸张的声明？请列出这些词语并解释。",
        "weight": 0.15
    },
    {
        "id": "rule3",
        "name": "语法错误检查",
        "description": "新闻标题是否包含错别字、语法错误、引号使用不当。",
        "prompt_template": "检查新闻标题'{title}'中是否存在错别字、语法错误或引号使用不当的情况？专业媒体很少出现这类错误。",
        "weight": 0.1
    },
    {
        "id": "rule4",
        "name": "常识合理性检查",
        "description": "新闻是否潜在地不合理或与常识相矛盾，或新闻更像八卦而不是事实报道。",
        "prompt_template": "分析新闻内容是否与常识相矛盾或不合理？内容是:\n'{content}'\n请指出不合理或违背常识的地方。",
        "weight": 0.2
    },
    {
        "id": "rule5",
        "name": "政治偏向性检查",
        "description": "新闻是否偏向于特定的政治观点，旨在影响公众舆论而不是呈现客观信息。",
        "prompt_template": "分析新闻内容是否存在明显的政治偏向性，是否试图影响读者观点而非客观报道？内容是:\n'{content}'",
        "weight": 0.15
    },
    {
        "id": "rule6",
        "name": "信息一致性检查",
        "description": "是否存在其他在线资源包含任何不一致、矛盾或对立的内容。",
        "prompt_template": "根据你的知识库，'{title}'这一新闻主题是否有其他公开报道？是否存在与该新闻内容矛盾的公开信息？",
        "weight": 0.2
    }
]


def get_combined_prompt(news_data: Dict[str, Any]) -> str:
    """生成包含所有规则的完整提示词

    Args:
        news_data: 包含新闻信息的字典

    Returns:
        完整的提示词
    """
    # 提取新闻数据
    title = news_data.get("title", "")
    content = news_data.get("content", "")
    domain = news_data.get("domain", "未知来源")

    # 构建提示词前言
    prompt = f"""你是一位专业的新闻事实核查专家，请根据以下规则分析这篇新闻的真实性，并按照要求的格式输出结果。

新闻标题: "{title}"
新闻来源: {domain}
新闻内容: 
{content}

请逐条分析以下规则:
"""

    # 添加每条规则的分析要求
    for i, rule in enumerate(DETECTION_RULES):
        rule_prompt = rule["prompt_template"].format(
            title=title,
            content=content,
            domain=domain
        )
        prompt += f"\n规则{i + 1}: {rule['name']}\n{rule_prompt}\n"

    # 添加输出格式要求
    prompt += """
请按以下格式回答:
规则1: [符合/不符合] - <简短说明原因>
规则2: [符合/不符合] - <简短说明原因>
规则3: [符合/不符合] - <简短说明原因>
规则4: [符合/不符合] - <简短说明原因>
规则5: [符合/不符合] - <简短说明原因>
规则6: [符合/不符合] - <简短说明原因>

注意：当规则检测到风险时应回答[符合]，未检测到风险时应回答[不符合]。
例如：如果新闻标题包含情绪化词语，规则2应回答[符合]；如果不包含，则回答[不符合]。

综合结论: [0-100]% 可能性为虚假新闻 - <简短总结判断依据>
"""
    return prompt
