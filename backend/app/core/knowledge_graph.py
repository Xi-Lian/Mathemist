#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
from typing import List, Dict, Any

class KnowledgeGraph:
    def __init__(self, graph_path: str = None):
        if graph_path is None:
            graph_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                'knowledge_graph.json'
            )
        
        self.graph_path = graph_path
        self.nodes = []
        self.edges = []
        
        # 添加恒等变换相关的关键词
        self.identity_transform_keywords = [
            '和角公式', '差角公式', '倍角公式', '半角公式',
            '和差化积', '积化和差', '万能公式', '诱导公式',
            'sin(A+B)', 'cos(A+B)', 'tan(A+B)',
            'sin(2α)', 'cos(2α)', 'tan(2α)',
            'sin(α/2)', 'cos(α/2)', 'tan(α/2)',
            '恒等变换', '三角恒等变换', '三角变换'
        ]
        
        self._load_graph()
    
    def _load_graph(self):
        try:
            with open(self.graph_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.nodes = data.get('nodes', [])
            self.edges = data.get('edges', [])
            self._create_indexes()
            
        except Exception as e:
            print("加载知识图谱失败:", str(e)[:100])
    
    def _create_indexes(self):
        self._node_id_index = {node['id']: node for node in self.nodes}
        self._node_label_index = {}
        for node in self.nodes:
            label = node['label']
            if label not in self._node_label_index:
                self._node_label_index[label] = []
            self._node_label_index[label].append(node)
        
        self._keyword_index = {}
        for node in self.nodes:
            keywords = node.get('keywords', [])
            for keyword in keywords:
                if keyword not in self._keyword_index:
                    self._keyword_index[keyword] = []
                self._keyword_index[keyword].append(node)
    
    def get_node_count(self) -> int:
        return len(self.nodes)
    
    def get_edge_count(self) -> int:
        return len(self.edges)
    
    def _split_query(self, query: str) -> List[str]:
        parts = re.split(r'[,，\s]+', query)
        result = []
        for part in parts:
            if part:
                result.append(part)
                if len(part) > 5:
                    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', part)
                    for char_group in chinese_chars:
                        if len(char_group) >= 3:
                            result.append(char_group)
        return result
    
    def search_nodes_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        results = []
        keyword_lower = keyword.lower()
        
        for kw, nodes in self._keyword_index.items():
            if keyword_lower in kw.lower():
                results.extend(nodes)
        
        for label, nodes in self._node_label_index.items():
            if keyword_lower in label.lower():
                results.extend(nodes)
        
        seen = set()
        unique_results = []
        for node in results:
            node_id = node['id']
            if node_id not in seen:
                seen.add(node_id)
                unique_results.append(node)
        
        return unique_results
    
    def get_related_nodes(self, concept: str) -> List[str]:
        related = []
        
        query_parts = self._split_query(concept)
        
        for part in query_parts:
            nodes = self.search_nodes_by_keyword(part)
            
            for node in nodes:
                related.append(node['label'])
                
                parent_id = node.get('parent')
                if parent_id and parent_id in self._node_id_index:
                    related.append(self._node_id_index[parent_id]['label'])
                
                for child in self.nodes:
                    if child.get('parent') == node['id']:
                        related.append(child['label'])
        
        return sorted(list(set(related)))
    
    def expand_query(self, query: str) -> str:
        expanded_terms = [query]
        
        query_parts = self._split_query(query)
        
        for part in query_parts:
            related = self.get_related_nodes(part)
            expanded_terms.extend(related)
            
            nodes = self.search_nodes_by_keyword(part)
            for node in nodes:
                keywords = node.get('keywords', [])
                expanded_terms.extend(keywords)
        
        return ' '.join(sorted(list(set(expanded_terms))))
    
    def validate_concept_match(self, query: str, content: str) -> float:
        query_parts = self._split_query(query)
        all_concepts = set()
        
        for part in query_parts:
            concepts = self.get_related_nodes(part)
            all_concepts.update(concepts)
        
        content_lower = content.lower()
        
        match_count = 0
        for concept in all_concepts:
            if concept.lower() in content_lower:
                match_count += 1
        
        has_identity_keyword = False
        if '恒等变换' in query:
            has_identity_keyword = True
            identity_match = False
            for keyword in self.identity_transform_keywords:
                if keyword.lower() in content_lower:
                    match_count += 1
                    identity_match = True
            
            if not identity_match:
                match_count -= 0.5
        
        if not all_concepts:
            for part in query_parts:
                if part in content_lower:
                    match_count += 0.5
        
        if not all_concepts and not query_parts:
            return 0.5
        
        total_weight = len(all_concepts) if all_concepts else max(len(query_parts), 1)
        result = match_count / total_weight
        
        return max(0.0, result)
    
    # ==================== 通用KG匹配引擎 ====================
    def universal_match(self, query_themes: List[str]) -> Dict[str, Any]:
        """
        通用KG匹配引擎 - 适用于所有主题类型的增强型匹配方法
        
        匹配策略（按优先级）：
        1. 精确匹配（label和keyword完全相等）
        2. 前缀匹配（主题是label/keyword前缀，或反之）
        3. 包含匹配（主题在label/keyword中，或反之）
        4. 同义词匹配（通过同义词映射）
        5. 父节点匹配（向上查找）
        6. 子节点匹配（向下查找）
        
        Args:
            query_themes: 查询主题列表
            
        Returns:
            {
                "matched_nodes": List[Dict],  # 匹配的节点列表
                "labels": List[str],          # 所有匹配节点的label
                "keywords": List[str],        # 所有匹配节点的keywords
                "node_ids": List[str],        # 匹配节点ID
                "match_details": List[Dict]   # 匹配详情（用于调试）
            }
        """
        # 扩展同义词映射
        synonym_map = {
            "图象": "图像", "图像": "图像",
            "三角": "三角", "三角函数": "三角函数",
            "对数": "对数", "对数函数": "对数函数",
            "指数": "指数", "指数函数": "指数函数",
            "幂函数": "幂函数", "二次函数": "二次函数",
            "正弦": "正弦", "余弦": "余弦", "正切": "正切",
            "周期性": "周期", "奇偶性": "奇偶", "单调性": "单调",
            "恒等变换": "恒等变换", "三角恒等变换": "三角恒等变换",
        }
        
        matched_nodes = []
        match_details = []
        seen_node_ids = set()
        
        for theme in query_themes:
            if not theme or not theme.strip():
                continue
            
            theme_normalized = theme
            for src, dst in synonym_map.items():
                theme_normalized = theme_normalized.replace(src, dst)
            
            theme_lower = theme.lower()
            theme_norm_lower = theme_normalized.lower()
            
            # 1. 精确匹配（最高优先级）
            exact_matches = []
            
            # 精确匹配label
            if theme in self._node_label_index:
                exact_matches.extend(self._node_label_index[theme])
            if theme_normalized in self._node_label_index:
                exact_matches.extend(self._node_label_index[theme_normalized])
            
            # 精确匹配keyword
            if theme in self._keyword_index:
                exact_matches.extend(self._keyword_index[theme])
            if theme_normalized in self._keyword_index:
                exact_matches.extend(self._keyword_index[theme_normalized])
            
            for node in exact_matches:
                if node['id'] not in seen_node_ids:
                    seen_node_ids.add(node['id'])
                    matched_nodes.append(node)
                    match_details.append({
                        'theme': theme,
                        'node_label': node['label'],
                        'match_type': '精确匹配',
                        'score': 1.0
                    })
            
            # 2. 前缀匹配
            prefix_matches = []
            for label, nodes in self._node_label_index.items():
                label_norm = label
                for src, dst in synonym_map.items():
                    label_norm = label_norm.replace(src, dst)
                
                if (label.startswith(theme) or theme.startswith(label) or
                    label_norm.startswith(theme_normalized) or theme_normalized.startswith(label_norm)):
                    prefix_matches.extend(nodes)
            
            for kw, nodes in self._keyword_index.items():
                kw_norm = kw
                for src, dst in synonym_map.items():
                    kw_norm = kw_norm.replace(src, dst)
                
                if (kw.startswith(theme) or theme.startswith(kw) or
                    kw_norm.startswith(theme_normalized) or theme_normalized.startswith(kw_norm)):
                    prefix_matches.extend(nodes)
            
            for node in prefix_matches:
                if node['id'] not in seen_node_ids:
                    seen_node_ids.add(node['id'])
                    matched_nodes.append(node)
                    match_details.append({
                        'theme': theme,
                        'node_label': node['label'],
                        'match_type': '前缀匹配',
                        'score': 0.8
                    })
            
            # 3. 包含匹配
            contain_matches = []
            for label, nodes in self._node_label_index.items():
                if theme_lower in label.lower() or label.lower() in theme_lower:
                    contain_matches.extend(nodes)
            
            for kw, nodes in self._keyword_index.items():
                if theme_lower in kw.lower() or kw.lower() in theme_lower:
                    contain_matches.extend(nodes)
            
            for node in contain_matches:
                if node['id'] not in seen_node_ids:
                    seen_node_ids.add(node['id'])
                    matched_nodes.append(node)
                    match_details.append({
                        'theme': theme,
                        'node_label': node['label'],
                        'match_type': '包含匹配',
                        'score': 0.6
                    })
            
            # 4. 父节点匹配（向上查找）
            parent_matches = []
            for node in self.nodes:
                label = node.get('label', '')
                if theme_lower in label.lower() or label.lower() in theme_lower:
                    parent_id = node.get('parent')
                    if parent_id and parent_id in self._node_id_index:
                        parent_node = self._node_id_index[parent_id]
                        if parent_node['id'] not in seen_node_ids:
                            parent_matches.append(parent_node)
            
            for node in parent_matches:
                if node['id'] not in seen_node_ids:
                    seen_node_ids.add(node['id'])
                    matched_nodes.append(node)
                    match_details.append({
                        'theme': theme,
                        'node_label': node['label'],
                        'match_type': '父节点匹配',
                        'score': 0.5
                    })
            
            # 5. 子节点匹配（向下查找）
            child_matches = []
            for node in self.nodes:
                label = node.get('label', '')
                if theme_lower in label.lower() or label.lower() in theme_lower:
                    for child in self.nodes:
                        if child.get('parent') == node['id']:
                            if child['id'] not in seen_node_ids:
                                child_matches.append(child)
            
            for node in child_matches:
                if node['id'] not in seen_node_ids:
                    seen_node_ids.add(node['id'])
                    matched_nodes.append(node)
                    match_details.append({
                        'theme': theme,
                        'node_label': node['label'],
                        'match_type': '子节点匹配',
                        'score': 0.7
                    })
        
        # 收集所有labels和keywords
        all_labels = set()
        all_keywords = set()
        all_node_ids = []
        
        for node in matched_nodes:
            all_node_ids.append(node['id'])
            all_labels.add(node.get('label', ''))
            for kw in node.get('keywords', []):
                all_keywords.add(kw)
        
        return {
            "matched_nodes": matched_nodes,
            "labels": sorted(list(all_labels)),
            "keywords": sorted(list(all_keywords)),
            "node_ids": sorted(all_node_ids),
            "match_details": match_details
        }
    
    def get_descendant_labels_and_keywords(self, concept: str) -> Dict[str, Any]:
        """
        获取概念的所有后代节点的 label 和 keywords。
        用于扩展检索过滤时的匹配词，使"三角恒等变换"也能匹配"二倍角"、"诱导公式"等后代节点。

        Args:
            concept: 概念名称（label 或 keyword）

        Returns:
            {
                "labels": List[str],   # 所有后代节点的 label
                "keywords": List[str], # 所有后代节点的 keywords（去重）
                "node_ids": List[str] # 所有匹配的节点 id（含自身）
            }
        """
        # 1. 找到匹配的节点（可能是多个）
        matched_nodes = []
        concept_lower = concept.lower()

        # 先按 label 精确/模糊匹配
        for node in self.nodes:
            label = node.get('label', '')
            if concept_lower == label.lower() or concept_lower in label.lower():
                matched_nodes.append(node)

        # 再按 keyword 匹配
        for node in self.nodes:
            keywords = node.get('keywords', [])
            for kw in keywords:
                if concept_lower == kw.lower() or concept_lower in kw.lower():
                    if node not in matched_nodes:
                        matched_nodes.append(node)
                    break

        if not matched_nodes:
            return {"labels": [], "keywords": [], "node_ids": []}

        # 2. 对每个匹配节点，递归收集后代
        descendant_ids = set()
        all_labels = set()
        all_keywords = set()

        for node in matched_nodes:
            node_id = node['id']
            descendant_ids.add(node_id)
            all_labels.add(node.get('label', ''))

            # 把自身的 keywords 也加上
            for kw in node.get('keywords', []):
                all_keywords.add(kw)

            # 递归收集后代
            self._collect_descendants(node_id, descendant_ids, all_labels, all_keywords)

        return {
            "labels": sorted(list(all_labels)),
            "keywords": sorted(list(all_keywords)),
            "node_ids": sorted(list(descendant_ids)),
        }

    def _collect_descendants(self, node_id: str, visited: set, labels: set, keywords: set):
        """递归收集所有后代节点的 label 和 keyword"""
        for child in self.nodes:
            if child.get('parent') == node_id and child['id'] not in visited:
                visited.add(child['id'])
                labels.add(child.get('label', ''))
                for kw in child.get('keywords', []):
                    keywords.add(kw)
                # 继续递归
                self._collect_descendants(child['id'], visited, labels, keywords)

    def get_sibling_concepts(self, concept: str) -> List[str]:
        """
        获取与给定概念同级的兄弟概念（不兼容的主题）
        
        Args:
            concept: 概念名称
        
        Returns:
            兄弟概念列表
        """
        siblings = []
        
        query_parts = self._split_query(concept)
        
        for part in query_parts:
            nodes = self.search_nodes_by_keyword(part)
            
            for node in nodes:
                parent_id = node.get('parent')
                
                if parent_id and parent_id in self._node_id_index:
                    parent_node = self._node_id_index[parent_id]
                    
                    for sibling in self.nodes:
                        if sibling.get('parent') == parent_id and sibling['id'] != node['id']:
                            siblings.append(sibling['label'])
        
        return sorted(list(set(siblings)))

if __name__ == "__main__":
    kg = KnowledgeGraph()
    print("节点数:", kg.get_node_count())
    print("边数:", kg.get_edge_count())
    
    query = "三角函数恒等变换"
    parts = kg._split_query(query)
    print("\n分词测试:")
    print("原始查询:", query)
    print("分词结果:", parts)
    
    related = kg.get_related_nodes(query)
    print("\n与'%s'相关的概念:" % query)
    for i, concept in enumerate(related[:10]):
        print("  %d. %s" % (i+1, concept))
    
    expanded = kg.expand_query(query)
    print("\n扩展查询:", expanded[:100])