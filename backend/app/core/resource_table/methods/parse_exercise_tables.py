from .._shared import *


class _ParseExerciseTablesMixin:
    def parse_exercise_tables(self) -> List[Dict[str, str]]:
        """
        解析习题资源汇总表
        
        Returns:
            习题资源列表
        """
        exercise_folder = self.learning_resource_path / '习题'
        
        if not exercise_folder.exists():
            logger.warning(f"习题文件夹不存在: {exercise_folder}")
            return []
        
        all_exercises = []
        
        # 遍历习题文件夹中的所有.md文件
        for md_file in exercise_folder.rglob('*.md'):
            # 跳过目录文件
            if md_file.name in ['题目目录.md', '答案目录.md']:
                continue
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                data = self.parse_markdown_table(content)
                
                # 添加资源类型和文件路径
                for item in data:
                    item['resource_type'] = 'exercise'
                    item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                    
                    # 添加标题：从文件名或题干中提取
                    # 优先使用文件名（不包含扩展名）
                    title = md_file.stem
                    # 如果文件名是数字，尝试从文件路径中提取章节信息
                    if title.isdigit():
                        # 从文件路径中提取章节信息
                        path_parts = md_file.relative_to(self.learning_resource_path).parts
                        # 找到包含章节信息的部分（如"必修一第二章-二次函数与一元二次方程"）
                        for part in path_parts:
                            if '二次函数' in part or '函数' in part or '三角函数' in part or '指数函数' in part or '对数函数' in part or '幂函数' in part or '三角恒等' in part:
                                title = part
                                break
                    
                    # 特殊处理：如果文件路径包含三角恒等变换相关内容，添加到知识点中
                    source_file = str(md_file.relative_to(self.learning_resource_path))
                    if '三角恒等' in source_file or '恒等变换' in source_file or '恒等变化' in source_file:
                        # 优先使用'知识点'字段，其次使用'知识点标签'
                        knowledge_points = item.get('知识点', item.get('知识点标签', ''))
                        if '三角恒等变换' not in knowledge_points:
                            knowledge_points = knowledge_points + ';三角恒等变换' if knowledge_points else '三角恒等变换'
                        # 更新知识点字段
                        item['知识点'] = knowledge_points
                        if '知识点标签' not in item or not item['知识点标签']:
                            item['知识点标签'] = knowledge_points
                    # 如果标题太长，截取前50个字符
                    if len(title) > 50:
                        title = title[:50]
                    item['title'] = title
                    
                    # 添加应用题识别逻辑
                    # 检查题干内容，看看是否包含应用题特征
                    question = item.get('题干', '')
                    if question:
                        # 定义应用题特征关键词（只保留真正与应用场景相关的关键词）
                        application_keywords = [
                            '实际应用', '应用', '生活', '工程', '经济', '物理', '化学', '生物',
                            '建筑', '施工', '设计', '测量', '机械', '电力', '水利', '交通',
                            '购物', '消费', '工资', '收入', '支出', '成本', '利润', '收益',
                            '价格', '销售', '市场', '需求', '供给', '投资', '理财', '股票',
                            '债券', '利率', '利息', '人口增长', '放射性衰变', '指数增长', '指数衰减',
                            '周期性变化', '波形', '最优化', '最优解', '实际问题', '生活场景',
                            '经济问题', '工程问题', '物理问题', '化学问题', '生物问题'
                        ]
                        
                        # 检查题干是否包含应用题特征关键词
                        is_application = any(keyword in question for keyword in application_keywords)
                        
                        # 如果题干包含应用题特征，修改题目类型为"应用题"
                        if is_application:
                            original_type = item.get('题目类型', '')
                            # 在原有题目类型后添加"应用题"标识
                            if '应用题' not in original_type:
                                item['题目类型'] = f"{original_type},应用题" if original_type else "应用题"
                
                # V12.0改进2：为每个习题添加年级元数据
                grade_enricher = get_grade_enricher()
                for item in data:
                    grade_enricher.enrich_resource_grade(item)
                
                all_exercises.extend(data)
                logger.info(f"解析习题汇总表: {md_file.name}, 共{len(data)}条记录")
                
            except Exception as e:
                logger.error(f"解析习题文件失败: {md_file}, 错误: {e}")
        
        # V12.0改进2：记录年级分布统计
        if all_exercises:
            grade_stats = get_grade_enricher().get_grade_statistics(all_exercises)
            logger.info(f"习题年级分布: {grade_stats}")
        
        logger.info(f"解析习题汇总表完成，共{len(all_exercises)}条记录")
        return all_exercises
