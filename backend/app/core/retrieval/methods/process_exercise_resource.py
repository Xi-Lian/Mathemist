from .._shared import *


class _ProcessExerciseResourceMixin:
    def _process_exercise_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理习题资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        # 获取题目文件名
        filename = metadata.get('题目文件名', '')
        source_file = metadata.get('source_file', '')
        question = metadata.get('题干', '')
        answer = metadata.get('解析', '')
        difficulty = metadata.get('难度（1-5）', '') or metadata.get('难度', '')
        knowledge_tags = metadata.get('知识点', '') or metadata.get('知识点标签', '')
        usage_scene = metadata.get('适用场景', '')
        question_type = metadata.get('题目类型', '')
        
        if filename:
            # 有文件名，说明是图片题目
            resource['title'] = f"习题（图片）: {filename}"
            resource['content'] = f"题目类型：{question_type}\n题目描述：{question}\n知识点：{knowledge_tags}\n难度：{difficulty}\n适用场景：{usage_scene}\n解析：{answer}"
            resource['is_image_exercise'] = True
            resource['filename'] = filename
            resource['source'] = metadata.get('原文件云端链接', '') or metadata.get('云端链接', '') or source_file
        else:
            # 文字题目，显示完整题目
            resource['title'] = f"习题: {question_type}"
            resource['content'] = f"题目：{question}\n\n解析：{answer}\n知识点：{knowledge_tags}\n难度：{difficulty}\n适用场景：{usage_scene}"
            resource['is_image_exercise'] = False
            resource['source'] = metadata.get('原文件云端链接', '') or metadata.get('云端链接', '') or source_file
        
        # 添加所有字段到资源对象，以便后续匹配使用
        resource['question'] = question
        resource['answer'] = answer
        resource['difficulty'] = difficulty
        resource['knowledge_tags'] = knowledge_tags
        resource['usage_scene'] = usage_scene
        resource['question_type'] = question_type
