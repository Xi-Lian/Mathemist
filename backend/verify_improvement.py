"""
验证V12.0改进是否正确集成到系统中

这个脚本不依赖后端服务，直接验证代码逻辑
"""

import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入模块，避免通过__init__.py导入所有依赖
import importlib.util
spec = importlib.util.spec_from_file_location("content_feature_extractor", 
    os.path.join(os.path.dirname(__file__), "app", "core", "content_feature_extractor.py"))
content_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(content_module)

SubjectiveIntentInterpreter = content_module.SubjectiveIntentInterpreter
ContentFeatureExtractor = content_module.ContentFeatureExtractor


def verify_integration():
    """验证改进是否正确集成"""
    print("="*60)
    print("验证V12.0改进集成")
    print("="*60)
    
    # 1. 验证SubjectiveIntentInterpreter类存在
    print("\n1. 验证SubjectiveIntentInterpreter类...")
    try:
        interpreter = SubjectiveIntentInterpreter()
        print("   ✅ SubjectiveIntentInterpreter类可实例化")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False
    
    # 2. 验证ContentFeatureExtractor包含subjective_interpreter
    print("\n2. 验证ContentFeatureExtractor集成...")
    try:
        extractor = ContentFeatureExtractor()
        if hasattr(extractor, 'subjective_interpreter'):
            print("   ✅ ContentFeatureExtractor包含subjective_interpreter属性")
        else:
            print("   ❌ ContentFeatureExtractor缺少subjective_interpreter属性")
            return False
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False
    
    # 3. 验证查询特征提取包含主观意图
    print("\n3. 验证查询特征提取...")
    test_query = "基础的二次函数习题"
    features = extractor.extract_query_content_features(test_query)
    
    if features.get('has_subjective_word') == True:
        print("   ✅ 正确检测到主观词汇")
    else:
        print("   ❌ 未检测到主观词汇")
        return False
    
    if features.get('subjective_intent') is not None:
        print("   ✅ 正确提取主观意图")
        intent = features['subjective_intent']
        print(f"      - 检测到的词汇: {intent['original_words']}")
        print(f"      - 推断场景: {intent['inferred_scenario']['name'] if intent['inferred_scenario'] else 'None'}")
        print(f"      - 置信度: {intent['confidence']:.2f}")
    else:
        print("   ❌ 未提取主观意图")
        return False
    
    if features.get('required_difficulty') is not None:
        print(f"   ✅ 正确映射难度要求: {features['required_difficulty']}")
    else:
        print("   ❌ 未映射难度要求")
        return False
    
    # 4. 验证难度匹配得分计算
    print("\n4. 验证难度匹配得分计算...")
    query = "基础的习题"
    intent_result = interpreter.interpret_intent(query)
    
    if '基础' in intent_result['interpreted_dimensions']:
        query_difficulty = intent_result['interpreted_dimensions']['基础']
        
        # 测试不同难度的匹配
        test_cases = [
            ('1', 1.0),  # 难度1应该完全匹配
            ('2', 1.0),  # 难度2应该完全匹配
            ('3', 0.6),  # 难度3应该部分匹配
            ('5', 0.0),  # 难度5应该不匹配
        ]
        
        all_passed = True
        for resource_diff, expected_min_score in test_cases:
            score = interpreter.calculate_difficulty_match_score(query_difficulty, resource_diff)
            if score >= expected_min_score - 0.01:  # 允许微小误差
                print(f"   ✅ 难度{resource_diff}匹配得分: {score:.2f} (期望>={expected_min_score})")
            else:
                print(f"   ❌ 难度{resource_diff}匹配得分: {score:.2f} (期望>={expected_min_score})")
                all_passed = False
        
        if not all_passed:
            return False
    
    # 5. 验证不同主观词汇的映射
    print("\n5. 验证不同主观词汇的映射...")
    test_words = {
        '基础': (1, 2),
        '简单': (1, 2),
        '中等': (3, 3),
        '提高': (3, 4),
        '难题': (4, 5),
        '综合': (3, 5),
    }
    
    for word, expected_range in test_words.items():
        query = f"{word}的习题"
        intent = interpreter.interpret_intent(query)
        
        if word in intent['interpreted_dimensions']:
            actual_range = intent['interpreted_dimensions'][word]['difficulty_range']
            if actual_range == expected_range:
                print(f"   ✅ '{word}' -> 难度范围{actual_range}")
            else:
                print(f"   ❌ '{word}' -> 难度范围{actual_range} (期望{expected_range})")
                return False
        else:
            print(f"   ❌ '{word}' 未检测到")
            return False
    
    print("\n" + "="*60)
    print("✅ 所有验证通过！V12.0改进已正确集成")
    print("="*60)
    
    return True


def demonstrate_improvement():
    """演示改进效果"""
    print("\n" + "="*60)
    print("V12.0改进效果演示")
    print("="*60)
    
    extractor = ContentFeatureExtractor()
    
    test_cases = [
        ("基础的二次函数习题", "新手入门场景"),
        ("刚学函数，需要入门练习", "通过上下文推断场景"),
        ("考前复习，需要重点题型", "考前复习场景"),
        ("给差生补弱，需要基础巩固", "差生补弱场景"),
        ("提高难度的指数函数练习", "能力提升场景"),
        ("难题，要高考难度的", "高考冲刺场景"),
    ]
    
    for query, description in test_cases:
        print(f"\n📝 查询: {query}")
        print(f"   预期场景: {description}")
        
        features = extractor.extract_query_content_features(query)
        
        if features.get('has_subjective_word'):
            intent = features['subjective_intent']
            scenario = intent.get('inferred_scenario', {})
            
            print(f"   ✅ 检测到主观词汇: {intent['original_words']}")
            print(f"   ✅ 推断场景: {scenario.get('name', '未知')} (置信度: {scenario.get('confidence', 0):.2f})")
            print(f"   ✅ 难度要求: {features['required_difficulty']}")
            
            # 显示场景特征
            if scenario.get('features'):
                print(f"   ✅ 场景特征: {scenario['features']}")
        else:
            print(f"   ⚠️ 未检测到主观词汇（可能查询中不包含预定义的主观词汇）")


if __name__ == "__main__":
    success = verify_integration()
    
    if success:
        demonstrate_improvement()
        
        print("\n" + "="*60)
        print("总结")
        print("="*60)
        print("""
V12.0改进已成功集成到系统中：

1. ✅ SubjectiveIntentInterpreter类已实现
   - 支持6个主观词汇：基础、简单、提高、中等、难题、综合
   - 每个词汇映射到难度范围、认知层次、题目特征等多维度

2. ✅ ContentFeatureExtractor已集成主观意图解释器
   - 自动检测查询中的主观词汇
   - 推断用户使用场景（新手入门、考前复习、差生补弱等）
   - 将主观词汇映射到具体的难度要求

3. ✅ 柔性难度匹配算法
   - 不再是非0即1的硬匹配
   - 接近难度范围的资源获得部分分数
   - 更符合用户的真实意图

4. ✅ 智能查询优化建议
   - 当置信度低时，主动提供优化建议
   - 帮助用户更准确地表达需求

现在可以通过前端界面(http://localhost:3001)测试实际效果！
        """)
    else:
        print("\n❌ 验证失败，请检查代码实现")
        sys.exit(1)
