# -*- coding: utf-8 -*-
"""
中文情感分析测试
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'C:/Users/23994/risk_sentinel')

from risk_analyzer import RiskAnalyzer

# 创建分析器
analyzer = RiskAnalyzer()

print('='*60)
print('中文情感分析测试')
print('='*60)

test_cases = [
    ('正面案例', 'IF椰子水真的很好喝，强烈推荐！'),
    ('负面案例', '这个产品质量很差，非常失望！'),
    ('曝光新闻', '曝IF椰子水涉嫌掺水掺糖！实测糖分超标'),
    ('监管调查', '市场监管部门介入调查IF椰子水'),
    ('消费者质疑', '网友实测：IF椰子水甜味不正常 疑加糖'),
    ('中性态度', '一直在喝IF，没什么问题啊'),
    ('下架新闻', '超市已暂时下架IF椰子水相关产品'),
    ('企业声明', 'IF官方声明：产品符合标准 保留追责权利'),
    ('中性内容', '今天天气不错')
]

for label, text in test_cases:
    result = analyzer.analyze_sentiment(text)
    polarity = round(result['polarity'], 3)
    confidence = round(result['confidence'], 3)
    source = result.get('source', 'unknown')
    print("\n【" + label + "】" + text)
    print("    -> " + result['sentiment_label'] + " | 极性: " + str(polarity) + " | 置信度: " + str(confidence) + " | 来源: " + source)

print('\n' + '='*60)
print('说明:')
print('- 极性范围: -1(负面) 到 1(正面)')
print('- 置信度: 0-1，越高越可靠')
print('- 已配置百度API时会使用百度NLP，否则降级到TextBlob')
print('='*60)
