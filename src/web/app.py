import sys
import os
import gradio as gr
import json

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.detector import FakeNewsDetector
from config import WEB_CONFIG
from src.rules.detection_rules import DETECTION_RULES


def create_app():
    """创建Gradio Web应用"""

    detector = FakeNewsDetector()

    def detect_news(title, content, url=""):
        """处理用户输入并返回检测结果"""
        try:
            result = detector.detect({
                "title": title,
                "content": content,
                "url": url
            })

            # 构建UI友好的输出
            rules_output = ""
            for i, rule in enumerate(DETECTION_RULES):
                rule_id = f"rule{i + 1}"
                if rule_id in result["rules"]:
                    rule_data = result["rules"][rule_id]
                    # 当规则"符合"时表示有风险
                    verdict = "⚠️ 风险" if rule_data["verdict"] == "符合" else "✅ 正常"
                    rules_output += f"**规则{i + 1}: {rule['name']}** - {verdict}\n"
                    rules_output += f"> {rule_data['reason']}\n\n"

            # 构建综合结论
            risk_percentage = result["conclusion"]["risk_percentage"]
            risk_level = result["risk_level"]
            risk_color = {
                "高风险": "red",
                "中等风险": "orange",
                "低风险": "green"
            }.get(risk_level, "gray")

            conclusion = f"""
### 虚假新闻风险评估: <span style='color:{risk_color}'>{risk_percentage}% ({risk_level})</span>

**判断依据**: {result["conclusion"]["explanation"]}
            """

            return rules_output, conclusion
        except Exception as e:
            return f"处理出错: {str(e)}", "无法完成分析"

    # 设计UI界面
    # 设计UI界面
    with gr.Blocks(title=WEB_CONFIG["TITLE"], theme=WEB_CONFIG["THEME"]) as app:
        gr.Markdown(f"""
        # {WEB_CONFIG["TITLE"]}
        {WEB_CONFIG["DESCRIPTION"]}

        请输入新闻标题、内容和来源URL，系统将分析其真实性。
        """)

        with gr.Row():
            with gr.Column():
                # 输入区域
                title_input = gr.Textbox(label="新闻标题", placeholder="请输入完整新闻标题...")
                content_input = gr.Textbox(label="新闻内容", placeholder="请输入新闻正文...", lines=10)
                url_input = gr.Textbox(label="新闻来源URL (选填)",
                                       placeholder="例如: https://news.example.com/article")

                submit_btn = gr.Button("开始分析", variant="primary")

            with gr.Column():
                # 输出区域
                rules_output = gr.Markdown(label="规则分析结果")
                conclusion_output = gr.Markdown(label="综合结论")

        # 添加示例
        examples = [
            ["震惊！科学家发现外星人基地就在月球背面",
             "据未经证实的消息，NASA的一位匿名科学家透露，在月球背面发现了疑似外星人活动的痕迹！多张照片显示有类似建筑物的结构，科学界震惊！",
             "https://fakenews-example.com/moon-aliens"],
            ["卫健委通报：某市发现新型传染病，已有数百人感染",
             "近日，某市出现多例不明原因发热病例，症状包括高烧、咳嗽。卫健委尚未确认具体病原体，但已隔离相关患者。专家称无需恐慌，正在全力研究。",
             "https://health-news.cn/outbreak-report"],
        ]
        gr.Examples(examples, inputs=[title_input, content_input, url_input])

        # 绑定事件
        submit_btn.click(
            fn=detect_news,
            inputs=[title_input, content_input, url_input],
            outputs=[rules_output, conclusion_output]
        )

    return app

def launch_app():
    """启动Web应用"""
    app = create_app()
    app.launch(server_port=WEB_CONFIG["PORT"])

if __name__ == "__main__":
    launch_app()

