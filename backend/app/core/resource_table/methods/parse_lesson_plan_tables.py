from .._shared import *


class _ParseLessonPlanTablesMixin:
    def parse_lesson_plan_tables(
        self,
        limit: Optional[int] = None,
        boards: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        解析教案资源汇总表
        改进：从文件名和文件路径中提取章节和主题信息
        
        Returns:
            教案资源列表
        """
        cloud_lesson_plans = self._parse_cloud_lesson_plan_tables(limit=limit, boards=boards)
        if cloud_lesson_plans:
            return cloud_lesson_plans

        lesson_plan_folder = self.learning_resource_path / '教案'
        
        if not lesson_plan_folder.exists():
            logger.warning(f"教案文件夹不存在: {lesson_plan_folder}")
            return []
        
        all_lesson_plans = []
        
        # 遍历教案文件夹中的所有.md文件
        processed_count = 0
        for md_file in lesson_plan_folder.rglob('*.md'):
            if limit is not None and processed_count >= limit:
                break
            # 跳过理论卡片和共性整合文档
            if md_file.name in ['优秀教案共性整合（最终版）.md']:
                continue
            
            # 检查是否是理论卡片
            if '理论卡片' in md_file.name:
                continue
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 改进：从文件名中提取章节和主题信息
                filename = md_file.stem
                relative_path = md_file.relative_to(lesson_plan_folder)
                
                # 提取章节信息（如 "3.2.2"）
                import re
                chapter_match = re.match(r'(\d+\.\d+(?:\.\d+)?)', filename)
                chapter = chapter_match.group(1) if chapter_match else ''
                
                # 提取主题信息（如 "奇偶性"、"单调性"）
                # 从文件名中提取关键词
                topic_keywords = [
                    '单调性', '奇偶性', '周期性', '对称性', '最值', '最大值', '最小值',
                    '概念', '表示法', '性质', '应用', '图像', '图象',
                    '幂函数', '指数函数', '对数函数', '三角函数', '二次函数', '一次函数',
                    '诱导公式', '三角恒等变换', '零点', '二分法',
                    '任意角', '弧度制', '同角三角函数',
                    # 添加语义关联关键词
                    '抛物线', '顶点', '对称轴', '开口',
                    '方程', '方程求解', '解方程',
                    '实际应用', '生活应用', '数学建模',
                    '放射性衰变', '指数增长', '指数衰减',
                    '周期性变化', '波形', '正弦', '余弦', '正切'
                ]
                
                extracted_topics = []
                for keyword in topic_keywords:
                    if keyword in filename or keyword in str(relative_path):
                        extracted_topics.append(keyword)
                
                # 构建知识点标签
                knowledge_tags = ', '.join(extracted_topics) if extracted_topics else ''
                
                # 对于教案文件，始终使用完整内容，不解析表格
                # 教案文件中的表格是教学设计的一部分，不应该被单独解析
                item = {
                    'resource_type': 'lesson_plan',
                    'source_file': str(md_file.relative_to(self.learning_resource_path)),
                    'title': filename,
                    'content': content,  # 使用完整内容
                    '章节': chapter,
                    '知识点标签': knowledge_tags,
                    '文件名主题': extracted_topics[0] if extracted_topics else ''
                }
                # V12.0改进2：为教案添加年级元数据
                grade_enricher = get_grade_enricher()
                grade_enricher.enrich_resource_grade(item)
                
                all_lesson_plans.append(item)
                processed_count += 1
                
                logger.info(f"解析教案: {md_file.name}, 章节: {chapter}, 主题: {knowledge_tags}, 年级: {item.get('grade', '未知')}")
                
            except Exception as e:
                logger.error(f"解析教案文件失败: {md_file}, 错误: {e}")
        
        # V12.0改进2：记录年级分布统计
        if all_lesson_plans:
            grade_stats = get_grade_enricher().get_grade_statistics(all_lesson_plans)
            logger.info(f"教案年级分布: {grade_stats}")
        
        logger.info(f"解析教案汇总表完成，共{len(all_lesson_plans)}条记录")
        return all_lesson_plans
