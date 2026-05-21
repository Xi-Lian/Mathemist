from .._shared import *
import hashlib
from typing import List, Tuple


class _CheckThemeRelevanceWithLlmMixin:
    # 类级别的 LLM 缓存
    _llm_score_cache: Dict[str, float] = {}
    _cache_max_size: int = 1000
    
    def _get_llm_cache_key(self, theme: str, content: str) -> str:
        """生成缓存键"""
        key_string = f"{theme}:{content[:200]}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _check_theme_relevance_with_llm(self, theme: str, doc: str, meta: Dict[str, Any]) -> bool:
        """
        使用LLM动态判断资源是否与主题相关（兼容旧接口）
        
        Args:
            theme: 主题名称
            doc: 资源内容
            meta: 资源元数据
        
        Returns:
            是否相关
        """
        score = self._calculate_theme_relevance_score(theme, doc, meta)
        return score >= 0.6
    
    def _calculate_batch_theme_relevance_scores(self, theme: str, resources: List[Tuple[str, Dict[str, Any]]]) -> List[float]:
        """
        批量计算多个资源的主题相关性分数（一次LLM调用处理多个资源）
        
        Args:
            theme: 主题名称
            resources: 资源列表 [(content, meta), ...]
        
        Returns:
            相关性分数列表，与输入资源顺序对应
        """
        if not resources:
            return []
        
        # 分离已缓存和未缓存的资源
        cached_scores = []
        uncached_indices = []
        uncached_resources = []
        
        for i, (content, meta) in enumerate(resources):
            cache_key = self._get_llm_cache_key(theme, content)
            if cache_key in self._llm_score_cache:
                score = self._llm_score_cache[cache_key]
                cached_scores.append((i, score))
                title = meta.get("title", "未知标题")
                print(f"      💾 LLM缓存命中：'{title}' 与主题 '{theme}' -> {score:.2f}")
            else:
                uncached_indices.append(i)
                uncached_resources.append((content, meta))
        
        # 如果所有资源都已缓存，直接返回
        if not uncached_resources:
            result = [0.0] * len(resources)
            for i, score in cached_scores:
                result[i] = score
            return result
        
        try:
            # 获取模型
            model = model_config.get_model("intent")
            
            # 构建批量Prompt
            resources_text = "\n\n".join([
                f"资源{i+1}：\n标题：{meta.get('title', '')}\n内容：{content[:300]}\n知识点：{meta.get('知识点', '')}"
                for i, (content, meta) in enumerate(uncached_resources)
            ])
            
            prompt = ChatPromptTemplate.from_template("""
你是数学教育资源评估专家。请评估以下多个资源与指定主题的相关性。

主题：{theme}

资源列表：
{resources_text}

评分标准：
- 1.0：资源完全围绕该主题，是核心内容
- 0.8-0.9：资源与主题高度相关
- 0.6-0.7：资源与主题中等相关
- 0.4-0.5：资源与主题弱相关
- 0.0-0.3：资源与主题基本无关

请按顺序返回每个资源的相关性分数（0-1之间），用逗号分隔，只返回数字，不要任何解释。
示例输出：0.9, 0.7, 0.3
""")
            
            # 一次调用处理所有未缓存的资源
            chain = prompt | model | StrOutputParser()
            result = chain.invoke({
                "theme": theme,
                "resources_text": resources_text
            })
            
            # 解析结果
            raw_scores = result.strip().split(',')
            scores = []
            for i, raw_score in enumerate(raw_scores):
                try:
                    score = max(0.0, min(1.0, float(raw_score.strip())))
                except ValueError:
                    score = 0.3
                scores.append(score)
                
                # 保存到缓存
                content, meta = uncached_resources[i]
                cache_key = self._get_llm_cache_key(theme, content)
                if len(self._llm_score_cache) >= self._cache_max_size:
                    first_key = next(iter(self._llm_score_cache))
                    del self._llm_score_cache[first_key]
                self._llm_score_cache[cache_key] = score
                
                title = meta.get("title", "未知标题")
                print(f"      🔍 LLM批量评分：'{title}' 与主题 '{theme}' -> {score:.2f}")
            
            # 合并结果（保持原始顺序）
            final_result = [0.0] * len(resources)
            for i, score in cached_scores:
                final_result[i] = score
            for i, idx in enumerate(uncached_indices):
                final_result[idx] = scores[i] if i < len(scores) else 0.3
            
            return final_result
            
        except Exception as e:
            print(f"      ⚠️ LLM批量评分失败: {e}，返回默认分数0.3")
            # 如果批量调用失败，回退到逐个调用
            final_result = [0.0] * len(resources)
            for i, score in cached_scores:
                final_result[i] = score
            for i, idx in enumerate(uncached_indices):
                content, meta = uncached_resources[i]
                final_result[idx] = self._calculate_theme_relevance_score(theme, content, meta)
            return final_result
    
    def _calculate_multi_dimension_score(self, query: str, resource: Dict[str, Any], kg_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        多维度融合评分 - 综合多个因素进行评分
        
        维度权重：
        - LLM主题相关性：40%
        - KG知识点匹配：30%
        - 语义相似度：20%
        - 资源质量：10%
        
        Args:
            query: 查询主题
            resource: 资源对象
            kg_result: KG匹配结果（可选）
        
        Returns:
            {
                "final_score": 综合分数（0-1）,
                "llm_score": LLM主题相关性分数,
                "kg_score": KG知识点匹配分数,
                "semantic_score": 语义相似度分数,
                "quality_score": 资源质量分数
            }
        """
        scores = {}
        
        # 1. LLM主题相关性（40%）
        content = resource.get('content', '')
        meta_info = {
            "title": resource.get('title', ''),
            "知识点": resource.get('知识点', '')
        }
        scores['llm_score'] = self._calculate_theme_relevance_score(query, content, meta_info)
        
        # 2. KG知识点匹配（30%）
        scores['kg_score'] = self._calculate_kg_match_score(resource, kg_result)
        
        # 3. 语义相似度（20%）
        scores['semantic_score'] = self._calculate_semantic_similarity(query, resource)
        
        # 4. 资源质量（10%）
        scores['quality_score'] = self._calculate_resource_quality(resource)
        
        # 综合评分
        scores['final_score'] = (
            scores['llm_score'] * 0.4 +
            scores['kg_score'] * 0.3 +
            scores['semantic_score'] * 0.2 +
            scores['quality_score'] * 0.1
        )
        
        # 确保分数在0-1范围内
        scores['final_score'] = max(0.0, min(1.0, scores['final_score']))
        
        return scores
    
    def _calculate_kg_match_score(self, resource: Dict[str, Any], kg_result: Dict[str, Any] = None) -> float:
        """计算KG知识点匹配分数"""
        resource_kp = resource.get('知识点', '')
        
        if not resource_kp:
            return 0.0
        
        if not kg_result or not kg_result.get('keywords'):
            # 如果没有KG结果，尝试直接从资源知识点判断
            return 0.5
        
        # 计算知识点与匹配关键词的交集
        # 【V65.0改进】处理分号分隔的知识点标签，合并为完整表述
        resource_kp_str = str(resource_kp).strip()
        if ';' in resource_kp_str:
            parts = [p.strip() for p in resource_kp_str.split(';') if p.strip()]
            if len(parts) >= 2:
                merged_kp = parts[0]
                for part in parts[1:]:
                    merged_kp += f"的{part}"
                kp_set = {merged_kp}
            else:
                kp_set = {parts[0]} if parts else set()
        else:
            kp_set = {resource_kp_str} if resource_kp_str else set()
        
        matched_keywords = set(kg_result.get('keywords', []))
        
        if not kp_set or not matched_keywords:
            return 0.3
        
        intersection = kp_set.intersection(matched_keywords)
        
        if not intersection:
            return 0.2
        
        return min(1.0, len(intersection) / len(kp_set))
    
    def _calculate_semantic_similarity(self, query: str, resource: Dict[str, Any]) -> float:
        """计算语义相似度分数"""
        try:
            from app.core.model_config import model_config
            
            # 获取嵌入模型
            embed_model = model_config.get_embedding_model()
            
            # 计算查询嵌入
            query_embedding = embed_model.embed_query(query)
            
            # 计算资源嵌入（标题+内容）
            resource_text = f"{resource.get('title', '')} {resource.get('content', '')[:500]}"
            resource_embedding = embed_model.embed_query(resource_text)
            
            # 计算余弦相似度
            from sklearn.metrics.pairwise import cosine_similarity
            similarity = cosine_similarity([query_embedding], [resource_embedding])[0][0]
            
            return max(0.0, min(1.0, similarity))
        
        except Exception as e:
            # 如果计算失败，返回默认分数
            return 0.5
    
    def _calculate_resource_quality(self, resource: Dict[str, Any]) -> float:
        """计算资源质量分数"""
        score = 0.5  # 基础分
        
        # 1. 难度等级（中等难度通常质量较高）
        difficulty = resource.get('难度', resource.get('difficulty', ''))
        if difficulty:
            try:
                diff_num = float(difficulty)
                if 2 <= diff_num <= 4:
                    score += 0.15
            except:
                pass
        
        # 2. 题目类型（解答题通常质量较高）
        question_type = resource.get('题目类型', '')
        if '解答题' in question_type or '证明题' in question_type:
            score += 0.1
        
        # 3. 是否有解析
        content = resource.get('content', '')
        if '解析' in content or '答案' in content:
            score += 0.1
        
        # 4. 是否有解题思路
        if '解题思路' in content:
            score += 0.05
        
        return min(1.0, score)
    
    def _calculate_theme_relevance_score(self, theme: str, doc: str, meta: Dict[str, Any]) -> float:
        """
        使用LLM计算资源与主题的相关性分数（0-1）- 带缓存
        
        Args:
            theme: 主题名称
            doc: 资源内容
            meta: 资源元数据
        
        Returns:
            相关性分数（0-1），越接近1表示越相关
        """
        # 检查缓存
        cache_key = self._get_llm_cache_key(theme, doc)
        if cache_key in self._llm_score_cache:
            cached_score = self._llm_score_cache[cache_key]
            title = meta.get("title", "未知标题")
            print(f"      💾 LLM缓存命中：'{title}' 与主题 '{theme}' -> {cached_score:.2f}")
            return cached_score
        
        try:
            # 获取模型
            model = model_config.get_model("intent")
            
            # 构建提示词 - V14.0：返回相关性分数，更灵活
            prompt = ChatPromptTemplate.from_template("""
你是一个数学教育资源评估专家。请评估以下资源与指定主题的相关性，并返回一个0到1之间的分数。

主题：{theme}

资源信息：
- 标题：{title}
- 内容摘要：{content}
- 知识点：{knowledge_points}

评分标准：
- 1.0：资源完全围绕该主题，是该主题的核心内容
- 0.8-0.9：资源主要内容与该主题高度相关
- 0.6-0.7：资源内容与该主题中等相关
- 0.4-0.5：资源内容与该主题弱相关
- 0.0-0.3：资源与该主题基本无关或不相关

判断依据：
1. 资源的主要内容是否明确涉及该主题的核心概念和方法
2. 资源是否包含该主题的典型特征和关键词
3. 资源是否属于该主题的知识体系

注意事项：
- 如果资源只涉及通用的数学概念（如定义、性质、基本运算）而没有特定主题的具体内容，评分应低于0.3
- 如果资源涉及的是与目标主题无关的基础数学知识，评分应低于0.3
- 如果资源的主要内容和知识点与目标主题完全无关，评分应为0
- 如果资源涉及多个主题，只要主要内容或核心知识点与目标主题高度相关，应给予较高评分
- 判断时应优先考虑资源的核心内容和核心考点，而不是边缘性的背景知识

请只返回一个0到1之间的数字，不要返回任何解释性文字。
""")
            
            # 提取资源信息
            title = meta.get("title", "未知标题")
            content = doc[:500] if len(doc) > 500 else doc
            knowledge_points = meta.get("知识点", "")
            
            # 构建链
            chain = prompt | model | StrOutputParser()
            
            # 调用LLM
            result = chain.invoke({
                "theme": theme,
                "title": title,
                "content": content,
                "knowledge_points": knowledge_points
            })
            
            # 解析结果
            result = result.strip()
            try:
                score = float(result)
                # 确保分数在0-1范围内
                score = max(0.0, min(1.0, score))
            except ValueError:
                # 如果解析失败，尝试从文本中提取数字
                import re
                match = re.search(r'(\d+\.?\d*)', result)
                if match:
                    score = max(0.0, min(1.0, float(match.group(1))))
                else:
                    score = 0.3
            
            print(f"      🔍 LLM评分：'{title}' 与主题 '{theme}' -> {score:.2f}")
            
            # 保存到缓存
            if len(self._llm_score_cache) >= self._cache_max_size:
                # 如果缓存满了，删除最早的缓存
                first_key = next(iter(self._llm_score_cache))
                del self._llm_score_cache[first_key]
            self._llm_score_cache[cache_key] = score
            
            return score
            
        except Exception as e:
            print(f"      ⚠️ LLM评分失败: {e}，返回默认分数0.3")
            return 0.3
