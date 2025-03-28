import argparse
import json
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.detector import FakeNewsDetector
from src.web.app import launch_app


def run_tests(test_file_path):
    """运行测试用例

    Args:
        test_file_path: 测试用例文件路径
    """
    try:
        with open(test_file_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
    except Exception as e:
        print(f"读取测试用例失败: {e}")
        return

    detector = FakeNewsDetector()

    print(f"开始运行{len(test_cases)}个测试用例...")

    for i, test_case in enumerate(test_cases):
        print(f"\n====== 测试用例 {i + 1} ======")
        print(f"标题: {test_case['title']}")

        try:
            result = detector.detect(test_case)

            # 打印结果
            print(f"检测结果: {result['risk_level']} ({result['conclusion']['risk_percentage']}%)")
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
    """主入口函数"""
    parser = argparse.ArgumentParser(description="虚假新闻检测系统")
    parser.add_argument('--web', action='store_true', help="启动Web界面")
    parser.add_argument('--test', action='store_true', help="运行测试用例")
    parser.add_argument('--test-file', default='data/test_cases.json', help="测试文件路径")

    args = parser.parse_args()

    if args.test:
        run_tests(args.test_file)
    elif args.web:
        launch_app()
    else:
        print("请指定运行模式: --web 启动Web界面 或 --test 运行测试")


if __name__ == "__main__":
    main()
