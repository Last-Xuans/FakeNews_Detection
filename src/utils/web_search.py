import re
import json
import requests
import logging
from typing import List, Dict, Any
import unicodedata
import jieba

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebSearchValidator:
    """网络搜索验证工具类，用于验证时效性新闻的真实性"""
    
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        """初始化网络搜索验证器
        
        Args:
            api_key: Google Custom Search API的密钥
            search_engine_id: Google Custom Search Engine的ID
        """
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.trusted_domains = [
            # 国际主流媒体
            'bbc.com', 'bbc.co.uk', 'cnn.com', 'reuters.com', 'apnews.com', 
            'nytimes.com', 'washingtonpost.com', 'wsj.com', 'nbcnews.com',
            'abcnews.go.com', 'foxnews.com', 'theguardian.com', 'aljazeera.com',
            'france24.com', 'dw.com', 'euronews.com',
            
            # 中文主流媒体
            'xinhuanet.com', 'chinadaily.com.cn', 'people.com.cn', 'thepaper.cn', 
            'sina.com.cn', 'sohu.com', '163.com', 'qq.com', 'ifeng.com', 'caixin.com',
            'cctv.com', 'china.com.cn', 'gmw.cn', 'huanqiu.com',
            
            # 科技媒体
            'techcrunch.com', 'wired.com', 'theverge.com', 'engadget.com',
            'mashable.com', 'cnet.com', 'zdnet.com', 'arstechnica.com', 
            '36kr.com', 'geekpark.net', 'cnbeta.com', 'leiphone.com',
            
            # 财经媒体
            'ft.com', 'bloomberg.com', 'economist.com', 'forbes.com',
            'cnbc.com', 'businessinsider.com', 'marketwatch.com',
            'yicai.com', 'jiemian.com', 'nbd.com.cn', 'cls.cn'
        ]
    
    def extract_keywords(self, news_data: Dict[str, Any]) -> List[str]:
        """从新闻中提取关键搜索词
        
        Args:
            news_data: 新闻数据，包含标题和内容
            
        Returns:
            搜索关键词列表
        """
        title = news_data.get("title", "")
        content = news_data.get("content", "")
        content_first_para = content.split("\n")[0] if content else ""
        
        # 组合不同的搜索关键词组合，提高搜索效果
        keywords = []
        
        # 1. 使用标题作为第一个关键词（最重要）
        keywords.append(title)
        
        # 2. 使用jieba分词提取标题中的关键名词和实体
        # 对标题进行分词
        seg_words = jieba.cut(title)
        words = [word for word in seg_words if len(word) > 1]  # 过滤单字词
        
        # 如果分词结果足够，使用前4个词作为组合
        if len(words) >= 3:
            keywords.append(" ".join(words[:4]))
        
        # 3. 提取时间、地点、人物等关键信息
        # 人名和地名通常是连续的名词
        name_pattern = r'[A-Z][a-z]+\s+[A-Z][a-z]+'  # 英文人名
        places_pattern = r'(北京|上海|广州|深圳|天津|重庆|香港|澳门|台湾|美国|中国|日本|韩国|俄罗斯|英国|法国|德国|加拿大|澳大利亚)'
        
        # 提取英文人名
        eng_names = re.findall(name_pattern, title + " " + content_first_para)
        if eng_names:
            for name in eng_names[:2]:  # 只取前两个人名
                keywords.append(f"{name} {title[:20]}")
        
        # 提取中文地名
        places = re.findall(places_pattern, title + " " + content_first_para)
        if places:
            # 添加地点+标题组合进行搜索
            for place in places[:2]:  # 只取前两个地名
                keywords.append(f"{place} {title[:20]}")
        
        # 4. 提取数字（如日期、统计数据等）
        numbers = re.findall(r'\d+(?:\.\d+)?%?', title)
        if numbers:
            # 数字通常是重要信息点
            for num in numbers[:2]:
                keywords.append(f"{num} {title[:20]}")
        
        # 5. 添加标题+首段内容组合（增加语境信息）
        if len(content_first_para) > 20:
            keywords.append(f"{title} {content_first_para[:50]}")
            
        # 6. 为国际新闻添加多语言变体
        # 检测是否为国际新闻（简单判断）
        is_international = any(place in title + " " + content_first_para 
                             for place in ['美国', '日本', '韩国', '俄罗斯', '英国', '法国', '德国'])
        
        if is_international:
            # 为人名添加英文搜索
            # 使用Unicode规范化简化处理
            normalized_title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
            if normalized_title != title:  # 说明可能有非ASCII字符
                keywords.append(normalized_title)
        
        # 确保关键词列表去重
        unique_keywords = []
        for kw in keywords:
            if kw not in unique_keywords:
                unique_keywords.append(kw)
        
        logger.info(f"提取的搜索关键词: {unique_keywords[:3]}...")
        return unique_keywords
    
    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """使用Google搜索API执行网络搜索
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if not self.api_key or not self.search_engine_id:
            logger.warning("未配置Google Search API，无法执行网络搜索")
            return []
            
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.search_engine_id,
            'q': query,
            'num': num_results
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'items' not in data:
                logger.warning(f"搜索未返回结果: {data.get('error', {}).get('message', '未知错误')}")
                return []
                
            results = []
            for item in data['items']:
                result = {
                    'title': item.get('title'),
                    'link': item.get('link'),
                    'snippet': item.get('snippet'),
                    'domain': self._extract_domain(item.get('link', '')),
                    'is_trusted': False
                }
                
                # 判断来源是否可信
                if result['domain'] in self.trusted_domains:
                    result['is_trusted'] = True
                    
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"执行网络搜索时出错: {e}")
            return []
    
    def _extract_domain(self, url: str) -> str:
        """从URL中提取域名
        
        Args:
            url: 网址
            
        Returns:
            域名
        """
        try:
            import urllib.parse
            netloc = urllib.parse.urlparse(url).netloc
            
            # 去除www前缀和子域名，只保留主域名
            domain_parts = netloc.split('.')
            if len(domain_parts) > 2:
                if domain_parts[0] == 'www':
                    domain_parts = domain_parts[1:]
                if len(domain_parts) > 2:
                    domain_parts = domain_parts[-2:]
            
            return '.'.join(domain_parts)
        except:
            return ""
    
    def validate_news(self, news_data: Dict[str, Any], search_results: List[Dict[str, Any]] = None, max_results: int = 8) -> Dict[str, Any]:
        """验证新闻内容
        
        Args:
            news_data: 新闻数据，包含标题和内容
            search_results: 可选的预设搜索结果，为None时会自动执行搜索
            max_results: 搜索结果的最大数量，默认为8个结果
            
        Returns:
            验证结果
        """
        title = news_data.get("title", "")
        content = news_data.get("content", "")
        merged_text = f"{title} {content}"
        
        # 如果没有提供搜索结果，则执行搜索
        if search_results is None:
            search_results = []
            
            # 提取关键词
            keywords = self.extract_keywords(news_data)
            
            # 使用多个关键词组合进行搜索，增加搜索成功率
            for query in keywords[:4]:  # 限制使用前4个关键词以控制API调用次数
                results = self.search_web(query, num_results=max_results)
                
                # 合并不重复的搜索结果
                for result in results:
                    # 检查是否已经有相同的结果
                    if not any(r['link'] == result['link'] for r in search_results):
                        # 添加URL信息
                        result['url'] = result['link']
                        search_results.append(result)
                
                # 如果已经有足够的结果，就停止搜索
                if len(search_results) >= max_results:
                    break
        
        # 如果没有搜索结果，则返回无法验证
        if not search_results:
            logger.warning("未找到任何与新闻相关的网络搜索结果")
            return {
                "validation_results": {
                    "trusted_sources_count": 0,
                    "sources": [],
                    "consistency_score": 0
                },
                "explanation": "无法通过网络搜索找到相关信息，无法验证",
                "risk_adjustment": 0
            }
        
        # 分析搜索结果
        trusted_sources = [r for r in search_results if r.get('is_trusted', False)]
        untrusted_sources = [r for r in search_results if not r.get('is_trusted', False)]
        
        # 计算可信源结果的一致性
        consistency_scores = []
        matched_entities_count = 0
        matched_data_points_count = 0
        
        # 提取新闻中的实体和数据点
        news_entities = self._extract_entities(merged_text)
        news_data_points = self._extract_data_points(merged_text)
        
        # 对每个搜索结果计算一致性分数
        for result in search_results:
            snippet = result.get('snippet', '')
            
            # 计算实体匹配度
            entity_matches = self._match_entities(news_entities, snippet)
            matched_entities_count += entity_matches
            
            # 计算数据点匹配度
            data_matches = self._match_data_points(news_data_points, snippet)
            matched_data_points_count += data_matches
            
            # 计算详细匹配度（更精确的文本匹配）
            detail_matches = self._count_detail_matches(merged_text, snippet)
            
            # 综合计算一致性分数 (0-100)
            result_score = 0
            if len(news_entities) > 0:
                result_score += (entity_matches / len(news_entities)) * 40
            if len(news_data_points) > 0:
                result_score += (data_matches / len(news_data_points)) * 40
            result_score += detail_matches * 20
            
            # 限制在0-100范围内
            result_score = min(100, result_score)
            
            # 保存分数到搜索结果中
            result['consistency_score'] = result_score
            consistency_scores.append(result_score)
        
        # 计算总体一致性分数
        avg_consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0
        
        # 根据一致性分数和可信源的数量，调整风险评估
        trusted_count = len(trusted_sources)
        risk_adjustment = 0
        
        if trusted_count >= 3 and avg_consistency >= 70:
            # 多个可信源高度一致，大幅降低风险
            risk_adjustment = -15
            explanation = "多个可信来源证实了该新闻内容，大幅降低风险评估"
        elif trusted_count >= 1 and avg_consistency >= 50:
            # 至少一个可信源中等一致，适度降低风险
            risk_adjustment = -10
            explanation = "至少一个可信来源部分证实了该新闻内容，适度降低风险评估"
        elif trusted_count == 0 and avg_consistency >= 50:
            # 无可信源但一致性尚可，小幅降低风险
            risk_adjustment = -5
            explanation = "搜索结果与新闻内容部分一致，但缺乏权威来源，小幅降低风险评估"
        elif avg_consistency <= 20:
            # 一致性很低，内容可能有误，适度提高风险
            risk_adjustment = 10
            explanation = "搜索结果与新闻内容有较大差异，内容可能不准确，提高风险评估"
        elif trusted_count >= 1 and avg_consistency <= 30:
            # 可信源不一致，严重提高风险
            risk_adjustment = 15
            explanation = "可信来源与新闻内容有较大差异，内容可能失实，严重提高风险评估"
        else:
            # 情况不明，不调整风险
            risk_adjustment = 0
            explanation = "网络搜索结果无法确定新闻真实性，不调整风险评估"
        
        return {
            "validation_results": {
                "trusted_sources_count": trusted_count,
                "consistency_score": round(avg_consistency),
                "sources": [
                    {
                        "domain": source.get('domain', ''),
                        "title": source.get('title', ''),
                        "is_trusted": source.get('is_trusted', False),
                        "url": source.get('link', ''),
                        "snippet": source.get('snippet', '')
                    } 
                    for source in search_results[:max_results]  # 保留更多搜索结果
                ]
            },
            "explanation": explanation,
            "risk_adjustment": risk_adjustment
        }
    
    def _extract_entities(self, text: str) -> List[str]:
        """从文本中提取关键实体
        
        Args:
            text: 新闻文本
            
        Returns:
            实体列表
        """
        # 简化版实体提取，实际项目中建议使用NER工具
        # 1. 提取可能的人名（连续的大写字母开头词）
        person_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        
        # 2. 提取可能的组织名
        org_pattern = r'\b(?:[A-Z][a-z]*\.?\s*)+(?:公司|组织|机构|部门|委员会|集团|Corporation|Inc|Organization|Association|Company|Agency)\b'
        
        # 3. 提取中文人名和组织名（简化处理）
        zh_name_pattern = r'[\u4e00-\u9fa5]{2,3}(?:先生|女士|教授|总|长)'
        zh_org_pattern = r'[\u4e00-\u9fa5]{2,}(?:公司|组织|机构|部门|委员会|集团|局)'
        
        # 4. 提取地名
        place_pattern = r'\b[A-Z][a-z]+(?:市|省|州|县|镇|区|国)\b|[\u4e00-\u9fa5]{2,}(?:国|市|省|州|县|镇|区)'
        
        # 合并所有提取到的实体
        entities = []
        entities.extend(re.findall(person_pattern, text))
        entities.extend(re.findall(org_pattern, text))
        entities.extend(re.findall(zh_name_pattern, text))
        entities.extend(re.findall(zh_org_pattern, text))
        entities.extend(re.findall(place_pattern, text))
        
        # 去重
        return list(set(entities))
    
    def _extract_data_points(self, text: str) -> List[str]:
        """提取文本中的数据点
        
        Args:
            text: 新闻文本
            
        Returns:
            数据点列表
        """
        # 1. 提取数字及其单位
        number_unit_pattern = r'\d+(?:\.\d+)?%?(?:万|亿|千|美元|元|美金|港币|英镑|欧元|日元)?'
        
        # 2. 提取日期
        date_pattern = r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?|\d{1,2}[-/月]\d{1,2}日?'
        
        # 3. 提取时间段
        duration_pattern = r'\d+(?:分钟|小时|天|周|月|年)(?:内|前|后)?'
        
        data_points = []
        data_points.extend(re.findall(number_unit_pattern, text))
        data_points.extend(re.findall(date_pattern, text))
        data_points.extend(re.findall(duration_pattern, text))
        
        return list(set(data_points))
    
    def _match_entities(self, entities: List[str], text: str) -> int:
        """计算实体匹配数
        
        Args:
            entities: 实体列表
            text: 待匹配文本
            
        Returns:
            匹配数量
        """
        match_count = 0
        for entity in entities:
            # 为了提高匹配率，做一些简单的预处理
            # 去除一些常见后缀
            clean_entity = re.sub(r'(先生|女士|教授|总|长|公司|组织|机构|部门|委员会|集团|局|市|省|州|县|镇|区|国)$', '', entity)
            if len(clean_entity) >= 2 and (clean_entity in text or entity in text):
                match_count += 1
        
        return match_count
    
    def _match_data_points(self, data_points: List[str], text: str) -> int:
        """计算数据点匹配数
        
        Args:
            data_points: 数据点列表
            text: 待匹配文本
            
        Returns:
            匹配数量
        """
        match_count = 0
        for data in data_points:
            if data in text:
                match_count += 1
        
        return match_count
        
    def _count_detail_matches(self, news_text: str, snippet: str) -> int:
        """计算新闻文本与搜索结果片段的细节匹配数
        
        Args:
            news_text: 新闻文本
            snippet: 搜索结果片段
            
        Returns:
            匹配数量
        """
        # 提取重要的命名实体（简化版）
        # 实际项目中应使用NER工具提取实体并比较
        
        # 简单的数字匹配（如日期、伤亡人数等）
        numbers_in_news = set(re.findall(r'\d+', news_text))
        numbers_in_snippet = set(re.findall(r'\d+', snippet))
        number_matches = len(numbers_in_news.intersection(numbers_in_snippet))
        
        # 人名、地名等实体匹配
        words_in_news = set(re.findall(r'\b[A-Z][a-z]{2,}\b', news_text))
        words_in_snippet = set(re.findall(r'\b[A-Z][a-z]{2,}\b', snippet))
        entity_matches = len(words_in_news.intersection(words_in_snippet))
        
        # 中文关键词匹配
        cn_keywords = []
        if re.search(r'[\u4e00-\u9fa5]', news_text): # 如果包含中文
            # 分词并提取较长的词（更可能是关键词）
            words = jieba.cut(news_text)
            cn_keywords = [w for w in words if len(w) >= 2 and re.search(r'[\u4e00-\u9fa5]', w)]
            
        cn_matches = 0
        for kw in cn_keywords:
            if kw in snippet:
                cn_matches += 1
        
        return number_matches + entity_matches + cn_matches 