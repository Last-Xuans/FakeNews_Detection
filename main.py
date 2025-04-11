import argparse
import json
import sys
import os
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到系统路径，确保能够正确导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.detector import FakeNewsDetector
from src.web.app import launch_app
from config import GOOGLE_SEARCH_CONFIG, WEB_CONFIG

# 从环境变量中读取Google API配置
google_api_key = os.getenv("GOOGLE_API_KEY", "")
google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
enable_search = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"

# 检查大模型API配置
llm_api_key = os.getenv("LLM_API_KEY", "")
llm_api_url = os.getenv("LLM_API_URL", "")
llm_model = os.getenv("LLM_MODEL", "")

# 显示当前API配置
if llm_api_key:
    masked_key = llm_api_key[:4] + "****" + llm_api_key[-4:] if len(llm_api_key) > 8 else "****"
    print(f"当前API配置: URL={llm_api_url}, MODEL={llm_model}, KEY={masked_key}")
else:
    logger.warning("未配置LLM API信息，系统将无法运行")
    print("错误: 未配置LLM API信息，请在.env中添加必要的配置")
    sys.exit(1)

def run_tests(test_file_path, enable_web_search=False):
    """运行测试用例

    Args:
        test_file_path: 测试用例文件路径
        enable_web_search: 是否启用网络搜索验证
    """
    try:
        with open(test_file_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
    except Exception as e:
        print(f"读取测试用例失败: {e}")
        return

    # 创建检测器，根据配置决定是否启用网络搜索
    detector = FakeNewsDetector(
        enable_web_search=enable_web_search,
        google_api_key=GOOGLE_SEARCH_CONFIG["API_KEY"],
        search_engine_id=GOOGLE_SEARCH_CONFIG["SEARCH_ENGINE_ID"]
    )

    print(f"开始运行{len(test_cases)}个测试用例..." + 
          (f" (启用网络搜索验证)" if enable_web_search else ""))

    for i, test_case in enumerate(test_cases):
        print(f"\n====== 测试用例 {i + 1} ======")
        print(f"标题: {test_case['title']}")

        try:
            result = detector.detect(test_case)

            # 打印结果
            print(f"检测结果: {result['risk_level']} ({result['conclusion']['risk_percentage']}%)")
            if enable_web_search and 'web_validation' in result:
                print(f"网络验证: {result['web_validation']['explanation']}")
            print(f"预期结果: {test_case['expected_result']['risk_level']}")

            # 简单验证
            if result['risk_level'] == test_case['expected_result']['risk_level']:
                print("✅ 测试通过!")
            else:
                print("❌ 测试失败!")
        except Exception as e:
            print(f"测试出错: {e}")

    print("\n测试完成!")

def main():
    """程序入口函数"""
    
    parser = argparse.ArgumentParser(description='虚假新闻检测系统')
    parser.add_argument('--web', action='store_true', help='启动Web界面')
    parser.add_argument('--web-search', action='store_true', help='启用网络搜索验证功能')
    parser.add_argument('--port', type=int, help='指定Web服务端口')
    
    args = parser.parse_args()
    
    # 检查是否启用Web界面
    if args.web:
        # 基于命令行参数与环境变量决定是否启用网络搜索
        # 如果命令行参数指定了web-search，或者环境变量ENABLE_WEB_SEARCH为true
        web_search_enabled = args.web_search or enable_search
        
        # 检查是否有Google API配置
        if web_search_enabled:
            # 检查API密钥是否配置正确
            if not google_api_key or not google_search_engine_id:
                logger.warning("网络搜索功能已启用，但Google API信息不完整，将禁用网络搜索功能")
                print("警告: 要启用网络搜索验证功能，请在.env中配置GOOGLE_API_KEY和GOOGLE_SEARCH_ENGINE_ID")
                web_search_enabled = False
            else:
                print("网络搜索验证功能已启用，但用户可以在界面中通过按钮选择是否使用")
                
        # 启动Web应用
        launch_app(enable_web_search=web_search_enabled, port=args.port)
    else:
        # 如果没有指定Web模式，显示帮助信息
        parser.print_help()
        print("\n推荐使用Web界面模式: python main.py --web")

if __name__ == "__main__":
    main()
