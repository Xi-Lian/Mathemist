from .._shared import *


class _ParseExcellentCaseTableMixin:
    def parse_excellent_case_table(self) -> List[Dict[str, str]]:
        """
        解析优秀案例分析文件汇总表
        
        Returns:
            优秀案例分析资源列表
        """
        excellent_case_file = self.learning_resource_path / '优秀案例分析文件汇总表.csv'
        
        if not excellent_case_file.exists():
            logger.warning(f"优秀案例分析文件汇总表不存在: {excellent_case_file}")
            return []
        
        all_excellent_cases = []
        
        try:
            encoding = self._detect_csv_encoding(str(excellent_case_file))
            with open(excellent_case_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    filename = row.get('文件名', '')
                    file_type = row.get('文件类型', '')
                    cloud_url = row.get('云端链接', '')
                    
                    # 只处理Markdown文件
                    if not (filename.endswith('.md') or file_type == 'Markdown文件'):
                        continue
                    
                    # 下载Markdown内容
                    content = self._download_cloud_markdown(cloud_url)
                    content_source = "cloud_markdown"
                    if not content:
                        logger.warning(f"优秀案例分析Markdown缺失: {filename}")
                        content = f"优秀案例分析: {filename}"
                        content_source = "index_fallback"
                    
                    # 提取章节和主题信息
                    full_text = f"{filename} {cloud_url}"
                    chapter_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', full_text)
                    chapter = chapter_match.group(1) if chapter_match else ''
                    
                    # 提取主题信息
                    topic_keywords = [
                        '充分条件', '必要条件', '随机变量', '分布列', '二次函数', '一元二次方程',
                        '不等式', '二项式定理', '全概率公式', '导数', '数列', '椭圆', '标准方程'
                    ]
                    
                    extracted_topics = []
                    for keyword in topic_keywords:
                        if keyword in filename:
                            extracted_topics.append(keyword)
                    
                    item = {
                        'resource_type': 'excellent_case',
                        'source_file': str(excellent_case_file.relative_to(self.learning_resource_path)),
                        'title': Path(filename).stem,
                        'content': content,
                        '章节': chapter,
                        '知识点标签': ', '.join(extracted_topics) if extracted_topics else '',
                        '文件名主题': extracted_topics[0] if extracted_topics else '',
                        '文件名': filename,
                        '文件类型': file_type,
                        '云端链接': cloud_url,
                        'content_source': content_source
                    }
                    
                    # 添加年级元数据
                    grade_enricher = get_grade_enricher()
                    grade_enricher.enrich_resource_grade(item)
                    
                    all_excellent_cases.append(item)
                    logger.info(f"解析优秀案例分析: {filename}, 章节: {chapter}, 主题: {', '.join(extracted_topics)}")
                    
        except Exception as e:
            logger.error(f"解析优秀案例分析文件汇总表失败: {e}")
            return []
        
        if all_excellent_cases:
            grade_stats = get_grade_enricher().get_grade_statistics(all_excellent_cases)
            logger.info(f"优秀案例分析年级分布: {grade_stats}")
        
        logger.info(f"解析优秀案例分析文件汇总表完成，共{len(all_excellent_cases)}条记录")
        return all_excellent_cases