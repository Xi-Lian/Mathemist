from .._shared import *


class _FormatResourceForSearchMixin:
    def format_resource_for_search(self, resource: Dict[str, str]) -> str:
        """
        将资源格式化为用于搜索的文本

        Args:
            resource: 资源字典

        Returns:
            格式化后的文本
        """
        resource_type = resource.get('resource_type', '')

        if resource_type == 'ggb':
            # 增强GGB资源的搜索文本，包含所有指定字段
            chapter = resource.get('章节', '')
            textbook = resource.get('教材', '')
            filename = resource.get('ggb文件名', '')
            steps = resource.get('演示步骤', '')
            purpose = resource.get('教学用途', '')
            
            # 构建更丰富的搜索文本，确保所有字段都被使用
            search_parts = ['GGB资源']
            if chapter:
                search_parts.append(f"章节：{chapter}")
            if textbook:
                search_parts.append(f"教材：{textbook}")
            if filename:
                search_parts.append(f"文件名：{filename}")
            if steps:
                search_parts.append(f"演示步骤：{steps}")
            if purpose:
                search_parts.append(f"教学用途：{purpose}")
            
            # 使用增强方法动态添加关键词
            base_text = "，".join(search_parts)
            enhanced_text = self._enhance_search_text(base_text, 'ggb', resource)
            
            return enhanced_text

        elif resource_type == 'syllabus':
            # 增强教学大纲资源的搜索文本，使用更多字段
            chapter = resource.get('章节', '')
            task = resource.get('教学任务（教学内容）', '')
            source_file = resource.get('source_file', '')
            filename = resource.get('文件名', '')
            
            # 构建基础搜索文本，包含更多字段
            search_parts = ['教学大纲']
            if chapter:
                search_parts.append(f"章节：{chapter}")
            if task:
                search_parts.append(f"教学任务：{task}")
            if filename:
                search_parts.append(f"文件名：{filename}")
            
            # 使用增强方法动态添加关键词
            base_text = "，".join(search_parts)
            enhanced_text = self._enhance_search_text(base_text, 'syllabus', resource)
            
            return enhanced_text

        elif resource_type == 'exercise':
            # 习题搜索文本：原始字段 + analysis，图片文件名不加入搜索文本
            question = resource.get('题干', '')
            filename = resource.get('题目文件名', '')       # 图片文件名，仅用于界面显示，不加入搜索文本
            source_file = resource.get('source_file', '')
            question_type = resource.get('题目类型', '')    # 原始字段：题目类型
            difficulty_raw = resource.get('难度（1-5）', resource.get('难度', ''))
            knowledge_tag = resource.get('知识点标签', '')  # 原始字段：知识点标签
            analysis_text_raw = resource.get('解析', '')   # 原始字段：解析（可能是png文件名或完整文本）
            scenario = resource.get('适用场景', '')
            analysis = resource.get('analysis', {})

            # 构建搜索文本
            search_parts = ['习题']

            # 1. 题目类型：原始字段 + analysis 一起用（去重）
            type_parts = []
            if question_type:
                type_parts.append(question_type)
            if analysis and isinstance(analysis, dict):
                analysis_type = analysis.get('题型', '')
                if analysis_type and analysis_type not in type_parts:
                    type_parts.append(analysis_type)
            if type_parts:
                search_parts.append(f"题目类型：{'，'.join(type_parts)}")

            # 2. 题干（原始字段，有文件名说明可能不完整，但仍纳入搜索文本）
            if question:
                search_parts.append(f"题目：{question}")

            # 3. 难度（原始字段）
            if difficulty_raw:
                difficulty_mapping = {
                    '1': '简单', '2': '较易', '3': '中等',
                    '4': '较难', '5': '困难'
                }
                difficulty_label = difficulty_mapping.get(str(difficulty_raw), str(difficulty_raw))
                search_parts.append(f"难度：{difficulty_raw}（{difficulty_label}）")

            # 4. 知识点标签：原始字段 + analysis 一起用（去重）
            kp_parts = []
            if knowledge_tag:
                # 【V65.0改进】处理分号分隔的知识点标签
                # 如果包含分号，将其合并为完整表述（如"函数单调性;区间判断" -> "函数单调性的区间判断"）
                # 【V101.0优化】同时保留原始知识点标签和合并后的版本，提高向量检索召回率
                knowledge_tag_str = str(knowledge_tag).strip()
                if ';' in knowledge_tag_str:
                    parts = [p.strip() for p in knowledge_tag_str.split(';') if p.strip()]
                    if len(parts) >= 2:
                        # 【V101.0新增】先添加每个独立的知识点标签（保持语义完整性）
                        for part in parts:
                            if part and part not in kp_parts:
                                kp_parts.append(part)
                        
                        # 再添加合并后的完整表述（用于语义匹配）
                        merged_kp = parts[0]
                        for part in parts[1:]:
                            merged_kp += f"的{part}"
                        if merged_kp and merged_kp not in kp_parts:
                            kp_parts.append(merged_kp)
                    else:
                        # 只有一个有效知识点
                        kp = parts[0] if parts else ''
                        if kp and kp not in kp_parts:
                            kp_parts.append(kp)
                else:
                    # 没有分号，直接添加
                    kp = knowledge_tag_str
                    if kp and kp not in kp_parts:
                        kp_parts.append(kp)
            if analysis and isinstance(analysis, dict):
                kp_list = analysis.get('知识点', [])
                if kp_list:
                    if isinstance(kp_list, list):
                        for kp in kp_list:
                            kp = str(kp).strip()
                            if kp and kp not in kp_parts:
                                kp_parts.append(kp)
                    else:
                        kp = str(kp_list).strip()
                        if kp and kp not in kp_parts:
                            kp_parts.append(kp)
            if kp_parts:
                search_parts.append(f"知识点：{';'.join(kp_parts)}")

            # 5. 解析：如果是png文件名则不加入；如果是完整文本则加入
            if analysis_text_raw and not str(analysis_text_raw).lower().endswith('.png'):
                search_parts.append(f"解析：{analysis_text_raw}")
            # 如果解析是png文件名，解析内容在图片里，不加入搜索文本

            # 6. 适用场景（原始字段）
            if scenario:
                search_parts.append(f"适用场景：{scenario}")

            # 7. analysis中的额外信息（补充原始字段没有的内容）
            if analysis and isinstance(analysis, dict):
                core_point = analysis.get('核心考点', '')
                if core_point:
                    search_parts.append(f"核心考点：{core_point}")
                formulas = analysis.get('涉及公式', [])
                if formulas:
                    search_parts.extend([f"公式：{formula}" for formula in formulas])
                solution = analysis.get('解题思路', '')
                if solution:
                    search_parts.append(f"解题思路：{solution}")

            # 特殊处理：如果文件路径包含三角恒等变换相关内容，添加到知识点中
            if '三角恒等' in source_file or '恒等变换' in source_file or '恒等变化' in source_file:
                # 检查当前知识点部分是否已包含
                has_triangle = any('三角恒等变换' in part for part in search_parts if '知识点' in part)
                if not has_triangle:
                    # 追加到知识点部分
                    for idx, part in enumerate(search_parts):
                        if part.startswith('知识点：'):
                            search_parts[idx] = part + ';三角恒等变换'
                            break
                    else:
                        search_parts.append('知识点：三角恒等变换')

            if source_file:
                search_parts.append(f"来源：{source_file}")

            # 使用增强方法动态添加关键词
            base_text = "，".join(search_parts)
            enhanced_text = self._enhance_search_text(base_text, 'exercise', resource)

            return enhanced_text

        elif resource_type == 'lesson_plan':
            # 教案资源使用完整内容作为搜索文本，确保教案解析器能正确解析
            title = resource.get('title', '')
            chapter = resource.get('章节', '')
            knowledge_tags = resource.get('知识点标签', '')
            file_topic = resource.get('文件名主题', '')
            content = resource.get('content', '')  # 获取完整内容
            cloud_url = resource.get('原文件云端链接', '') or resource.get('云端链接', '')
            
            # 提取所有相关主题词
            search_parts = ['教案']

            # 增加文件名权重：在搜索文本开头多次重复文件名
            if title:
                # 重复标题3次，提高其在向量嵌入中的权重
                search_parts.extend([title, title, title])

            # 检查文件名主题
            if file_topic:
                # 重复文件名主题2次，提高其权重
                search_parts.extend([file_topic, file_topic])

            # 检查知识点标签
            if knowledge_tags:
                tags = [tag.strip() for tag in knowledge_tags.split(',')]
                for tag in tags:
                    if tag and tag not in search_parts:
                        search_parts.append(tag)

            # 添加章节
            if chapter:
                search_parts.append(f"章节：{chapter}")

            # 添加标题中的关键部分
            title_cleaned = title.replace('教学设计', '').replace('教案', '').replace('导学案', '').strip(' -（）()【】[]')
            if title_cleaned:
                search_parts.append(f"标题：{title_cleaned}")

            if cloud_url:
                search_parts.append(f"云端资源：{cloud_url}")

            # 添加完整内容，确保教案解析器能正确解析教学目标、教学过程、重难点
            if content:
                # 去除Markdown格式和图片引用，提高向量检索相似度
                import re
                # 去除图片引用 ![](image.png)
                content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
                # 去除图片引用 ![...](...) 格式
                content = re.sub(r'!\[.*?\]\[.*?\]', '', content)
                # 去除Markdown链接 [text](url)
                content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
                # 去除Markdown粗体 **text**
                content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
                # 去除Markdown斜体 *text*
                content = re.sub(r'\*([^*]+)\*', r'\1', content)
                # 去除Markdown标题 # text
                content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
                # 去除表格格式
                # 去除表格宽度高度信息 {width="..." height="..."}
                content = re.sub(r'\{width="[^"]*"\s+height="[^"]*"\}', '', content)
                content = re.sub(r'\{width="[^"]*"\}', '', content)
                content = re.sub(r'\{height="[^"]*"\}', '', content)
                # 去除表格分隔符行
                content = re.sub(r'\|?[-:]+\|?[-:]+\|?[-:]+\|?', '', content)
                content = re.sub(r'\+[-:]+\+[-:]+\+[-:]+\+', '', content)
                # 去除表格中的竖线分隔符
                content = re.sub(r'\|', '，', content)
                # 去除表格中的加号分隔符
                content = re.sub(r'\+', '，', content)
                # 去除表格中的横线分隔符
                content = re.sub(r'-+', '', content)
                # 去除表格中的冒号分隔符
                content = re.sub(r':+', '，', content)
                # 去除表格中的点号分隔符
                content = re.sub(r'\.+', '，', content)
                # 去除表格中的空格分隔符
                content = re.sub(r'\s+', ' ', content)
                # 去除表格中的特殊符号
                content = re.sub(r'[锛岋紝锛?锛?]+', '，', content)
                content = re.sub(r'[锛?锛?]+', '，', content)
                content = re.sub(r'[锛?锛?]+', '，', content)
                content = re.sub(r'[锛?锛?]+', '，', content)
                content = re.sub(r'[锛?锛?]+', '，', content)
                content = content.strip()
                
                # 增加内容长度限制到10000字符，确保教案解析器能正确解析
                max_content_length = 10000
                if len(content) > max_content_length:
                    content = content[:max_content_length] + '...'
                search_parts.append(f"内容：{content}")
            
            return '，'.join(search_parts)
        
        elif resource_type == 'theory':
            # 增强理论卡片资源的搜索文本
            title = resource.get('title', '')
            content = resource.get('content', '')
            filename = resource.get('文件名', '')
            
            # 构建更丰富的搜索文本
            search_parts = ['理论卡片']
            if title:
                search_parts.append(f"标题：{title}")
            if filename:
                search_parts.append(f"文件名：{filename}")
            if content:
                search_parts.append(f"内容：{content}")
            
            return '，'.join(search_parts)
        
        elif resource_type == 'courseware':
            # 增强课件资源的搜索文本，确保使用指定字段
            content = resource.get('内容', '')
            filename = resource.get('文件名', '')
            usage = resource.get('教学用途', '')
            source_file = resource.get('source_file', '')
            
            # 构建基础搜索文本，确保所有指定字段都被使用
            search_parts = ['课件']
            if content:
                search_parts.append(f"内容：{content}")
            if filename:
                search_parts.append(f"文件名：{filename}")
            if usage:
                search_parts.append(f"教学用途：{usage}")
            if source_file:
                search_parts.append(f"来源：{source_file}")
            
            # 使用增强方法动态添加关键词
            base_text = "，".join(search_parts)
            enhanced_text = self._enhance_search_text(base_text, 'courseware', resource)
            
            return enhanced_text
        
        elif resource_type == 'lesson_case':
            # 增强课例视频资源的搜索文本，使用更多字段
            chapter = resource.get('章节', '')
            filename = resource.get('视频文件名/网址', '')
            analysis = resource.get('分析', '')
            textbook = resource.get('教材', '')
            source_file = resource.get('source_file', '')
            
            # 构建基础搜索文本
            base_parts = []
            
            # 添加资源类型关键词
            base_parts.append("课例")
            base_parts.append("教学视频")
            base_parts.append("课堂实录")
            
            if textbook:
                base_parts.append(f"教材：{textbook}")
            
            if chapter:
                base_parts.append(f"章节：{chapter}")
            
            # 尝试从文件名中提取知识点信息
            if filename and not filename.startswith('http'):
                # 从文件名中提取关键信息
                topic_info = self._extract_topic_from_filename(filename)
                if topic_info:
                    base_parts.append(f"知识点：{topic_info}")
                base_parts.append(f"视频文件名：{filename}")
            elif filename:
                # 如果是网址，直接添加
                base_parts.append(f"视频网址：{filename}")
            
            if analysis and analysis.strip():
                base_parts.append(f"分析：{analysis}")
            
            if source_file:
                base_parts.append(f"来源：{source_file}")
            
            # 构建基础搜索文本
            base_text = '，'.join(base_parts)
            
            # 使用增强方法动态添加关键词
            enhanced_text = self._enhance_search_text(base_text, 'lesson_case', resource)
            
            return enhanced_text
        
        else:
            return str(resource)
