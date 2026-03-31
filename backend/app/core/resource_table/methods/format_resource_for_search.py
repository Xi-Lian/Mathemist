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
            # 增强GGB资源的搜索文本，包含更多字段
            chapter = resource.get('章节', '')
            textbook = resource.get('教材', '')
            filename = resource.get('ggb文件名', '')
            steps = resource.get('演示步骤', '')
            purpose = resource.get('教学用途', '')
            
            # 构建更丰富的搜索文本
            search_parts = []
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
            # V54.0改进：增强教学大纲资源的搜索文本
            chapter = resource.get('章节', '')
            task = resource.get('教学任务（教学内容）', '')
            source_file = resource.get('source_file', '')
            
            # 构建基础搜索文本
            base_text = f"章节：{chapter}，教学任务：{task}"
            
            # 使用增强方法动态添加关键词
            enhanced_text = self._enhance_search_text(base_text, 'syllabus', resource)
            
            return enhanced_text

        elif resource_type == 'exercise':
            # 习题资源特殊处理
            question = resource.get('题干', '')
            filename = resource.get('题目文件名', '')
            source_file = resource.get('source_file', '')

            # 优先使用'知识点'字段，其次使用'知识点标签'
            knowledge_points = resource.get('知识点', resource.get('知识点标签', ''))
            
            # 特殊处理：如果文件路径包含三角恒等变换相关内容，添加到知识点中
            if '三角恒等' in source_file or '恒等变换' in source_file or '恒等变化' in source_file:
                if '三角恒等变换' not in knowledge_points:
                    knowledge_points = knowledge_points + ';三角恒等变换' if knowledge_points else '三角恒等变换'

            # 如果有文件名，说明是图片题目
            if filename:
                base_text = f"题目类型：{resource.get('题目类型', '')}，题目描述：{question}，知识点：{knowledge_points}，来源：{source_file}"
            else:
                # 文字题目，显示完整题目
                base_text = f"题目类型：{resource.get('题目类型', '')}，题目：{question}，知识点：{knowledge_points}，来源：{source_file}"
            
            # 使用增强方法动态添加关键词
            enhanced_text = self._enhance_search_text(base_text, 'exercise', resource)
            
            return enhanced_text

        elif resource_type == 'lesson_plan':
            # V54.0改进：教案资源使用完整内容作为搜索文本，确保教案解析器能正确解析
            title = resource.get('title', '')
            chapter = resource.get('章节', '')
            knowledge_tags = resource.get('知识点标签', '')
            file_topic = resource.get('文件名主题', '')
            content = resource.get('content', '')  # 获取完整内容
            cloud_url = resource.get('原文件云端链接', '') or resource.get('云端链接', '')
            
            # 提取所有相关主题词
            search_parts = ['教案']

            # 首先检查标题中是否包含函数性质关键词
            function_properties = ['单调性', '奇偶性', '周期性', '最值', '最大值', '最小值', 
                                   '零点', '定义域', '值域', '解析式', '表示法', '概念']
            
            # 检查标题中是否包含函数性质关键词
            title_lower = title.lower()
            for prop in function_properties:
                if prop in title:
                    search_parts.append(f"函数的{prop}")
                    break

            # 检查文件名主题
            if file_topic:
                # 检查是否是函数的性质
                is_function_property = any(prop in file_topic for prop in function_properties)
                if is_function_property and '函数' not in file_topic:
                    search_parts.append(f"函数的{file_topic}")
                else:
                    search_parts.append(file_topic)

            # 检查知识点标签
            if knowledge_tags:
                tags = [tag.strip() for tag in knowledge_tags.split(',')]
                for tag in tags:
                    if tag and tag not in search_parts:
                        # 检查是否是函数的性质
                        is_function_property = any(prop in tag for prop in function_properties)
                        if is_function_property and '函数' not in tag:
                            search_parts.append(f"函数的{tag}")
                        else:
                            search_parts.append(tag)

            # 添加章节
            if chapter:
                search_parts.append(chapter)

            # 添加标题中的关键部分
            title_cleaned = title.replace('教学设计', '').replace('教案', '').replace('导学案', '').strip(' -（）()【】[]')
            if title_cleaned:
                search_parts.append(title_cleaned)

            if cloud_url:
                search_parts.append(f"云端资源：{cloud_url}")

            # 确保搜索文本包含函数性质关键词
            # 检查标题中是否包含函数性质关键词
            for prop in function_properties:
                if prop in title and f"函数的{prop}" not in search_parts:
                    search_parts.append(f"函数的{prop}")

            # V54.2改进：添加完整内容，确保教案解析器能正确解析教学目标、教学过程、重难点
            if content:
                # V54.3改进：去除Markdown格式和图片引用，提高向量检索相似度
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
                # V54.4改进：去除表格格式
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
                
                # V54.1改进：增加内容长度限制到10000字符，确保教案解析器能正确解析
                max_content_length = 10000
                if len(content) > max_content_length:
                    content = content[:max_content_length] + '...'
                search_parts.append(f"内容：{content}")
            
            return '，'.join(search_parts)
        
        elif resource_type == 'theory':
            return f"标题：{resource.get('title', '')}，内容：{resource.get('content', '')}"
        
        elif resource_type == 'courseware':
            # V54.0改进：增强课件资源的搜索文本
            content = resource.get('内容', '')
            filename = resource.get('文件名', '')
            usage = resource.get('教学用途', '')
            source_file = resource.get('source_file', '')
            
            # 构建基础搜索文本
            base_text = f"内容：{content}，文件名：{filename}，教学用途：{usage}"
            
            # 使用增强方法动态添加关键词
            enhanced_text = self._enhance_search_text(base_text, 'courseware', resource)
            
            return enhanced_text
        
        elif resource_type == 'lesson_case':
            # V54.0改进：增强课例视频资源的搜索文本
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
            
            if analysis and analysis.strip():
                base_parts.append(f"分析：{analysis}")
            elif filename:
                # 如果分析为空，从文件名中提取关键信息
                base_parts.append(f"视频：{filename}")
            
            # 构建基础搜索文本
            base_text = '，'.join(base_parts)
            
            # 使用增强方法动态添加关键词
            enhanced_text = self._enhance_search_text(base_text, 'lesson_case', resource)
            
            return enhanced_text
        
        else:
            return str(resource)
