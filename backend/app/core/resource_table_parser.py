"""
资源汇总表解析模块
用于解析learning_resource文件夹中的markdown表格数据

V12.0改进2：年级元数据体系重构
- 集成GradeMetadataEnricher自动推断年级信息

V54.0改进：动态关键词提取和资源格式化增强
- 添加通用关键词提取方法
- 增强教学大纲、课件、课例视频资源的搜索文本
- 动态从文件路径和内容中提取主题信息
"""

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from urllib.parse import urlsplit, urlunsplit
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# V12.0改进2：导入年级元数据丰富器
from .grade_metadata_enricher import get_grade_enricher


class ResourceTableParser:
    """资源汇总表解析器"""
    
    def __init__(self, learning_resource_path: str):
        """
        初始化解析器
        
        Args:
            learning_resource_path: learning_resource文件夹路径
        """
        # 确保learning_resource_path是绝对路径
        self.learning_resource_path = Path(learning_resource_path).resolve()
        self.project_root = self.learning_resource_path.parent if self.learning_resource_path.name == "learning_resource" else self.learning_resource_path
        self.lesson_plan_cache_dir = self.project_root / "backend" / "data" / "cloud_lesson_plan_cache"
        self.lesson_plan_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # V54.0改进：初始化关键词映射表
        self._init_keyword_mappings()

    def _detect_csv_encoding(self, csv_path: Path) -> str:
        """
        检测CSV编码，兼容UTF-8和GB系列编码
        """
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
            try:
                with open(csv_path, "r", encoding=encoding, newline="") as f:
                    reader = csv.reader(f)
                    header = next(reader, [])
                    if header:
                        return encoding
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        return "utf-8-sig"

    def _get_cloud_lesson_plan_csv_files(self) -> List[Path]:
        """
        获取根目录下的教案资源CSV索引文件
        """
        csv_files = sorted(self.project_root.glob("*教案资源信息汇总表.csv"))
        return [path for path in csv_files if path.is_file()]

    def _load_cloud_lesson_plan_index(self) -> List[Dict[str, str]]:
        """
        读取教案资源CSV索引
        """
        rows: List[Dict[str, str]] = []
        for csv_path in self._get_cloud_lesson_plan_csv_files():
            encoding = self._detect_csv_encoding(csv_path)
            domain_name = csv_path.stem.replace("-教案资源信息汇总表", "")
            try:
                with open(csv_path, "r", encoding=encoding, newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        normalized = {str(k).strip(): (str(v).strip() if v is not None else "") for k, v in row.items() if k}
                        if not normalized.get("文件名"):
                            continue
                        normalized["索引文件"] = csv_path.name
                        normalized["板块"] = domain_name
                        rows.append(normalized)
                logger.info(f"读取云端教案索引: {csv_path.name}, 编码={encoding}, 记录数={sum(1 for row in rows if row.get('索引文件') == csv_path.name)}")
            except Exception as e:
                logger.error(f"读取云端教案索引失败: {csv_path}, 错误: {e}")
        return rows

    def _build_logical_lesson_plan_path(self, row: Dict[str, str]) -> str:
        """
        为云端教案记录构建逻辑路径，兼容现有路径推断逻辑
        """
        board = row.get("板块", "")
        directory = row.get("目录", "").replace("\\", "/").strip("/")
        filename = row.get("文件名", "")
        parts = ["教案"]
        if board:
            parts.append(board)
        if directory:
            parts.append(directory)
        if filename:
            parts.append(filename)
        return "/".join(part for part in parts if part)

    def _normalize_filename_key(self, filename: str) -> str:
        """
        规范化文件名，便于关联md与原文件
        """
        return Path((filename or "").strip()).stem.lower()

    def _find_linked_lesson_plan_row(
        self,
        row: Dict[str, str],
        rows_by_path: Dict[str, Dict[str, str]],
        rows_by_name: Dict[str, List[Dict[str, str]]]
    ) -> Optional[Dict[str, str]]:
        """
        为Markdown记录查找关联的原始教案文件
        """
        linked_filename = row.get("关联文件", "").strip()
        logical_path = self._build_logical_lesson_plan_path(row)

        if linked_filename:
            linked_logical_path = "/".join(logical_path.split("/")[:-1] + [linked_filename])
            linked_row = rows_by_path.get(linked_logical_path.lower())
            if linked_row:
                return linked_row

        # 回退策略：同目录下根据去扩展名匹配doc/docx/pdf原文件
        stem_key = self._normalize_filename_key(row.get("文件名", ""))
        directory = row.get("目录", "").replace("\\", "/").strip("/").lower()
        candidates = rows_by_name.get(stem_key, [])
        preferred_exts = {".doc", ".docx", "doc", "docx", ".pdf", "pdf"}
        for candidate in candidates:
            candidate_ext = candidate.get("扩展名", "").lower()
            candidate_dir = candidate.get("目录", "").replace("\\", "/").strip("/").lower()
            if candidate_dir == directory and candidate_ext in preferred_exts:
                return candidate

        return None

    def _download_cloud_markdown(self, url: str) -> str:
        """
        下载云端Markdown内容，并做本地缓存
        """
        if not url:
            return ""

        cache_key = hashlib.md5(url.encode("utf-8")).hexdigest()
        cache_file = self.lesson_plan_cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                return cached.get("content", "")
            except Exception:
                logger.warning(f"读取教案缓存失败，重新下载: {cache_file}")

        try:
            with urlopen(url, timeout=20) as response:
                raw = response.read()
            for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
                try:
                    content = raw.decode(encoding)
                    break
                except UnicodeDecodeError:
                    content = ""
            if not content:
                content = raw.decode("utf-8", errors="ignore")

            cache_file.write_text(
                json.dumps({"url": url, "content": content}, ensure_ascii=False),
                encoding="utf-8"
            )
            return content
        except (HTTPError, URLError, TimeoutError) as e:
            logger.error(f"下载云端Markdown失败: {url}, 错误: {e}")
            return ""
        except Exception as e:
            logger.error(f"下载云端Markdown异常: {url}, 错误: {e}")
            return ""

    def _derive_markdown_url(self, markdown_filename: str, linked_row: Optional[Dict[str, str]]) -> str:
        """
        当Markdown行缺少云端链接时，根据原文件链接推导Markdown链接
        """
        if not linked_row:
            return ""

        original_url = linked_row.get("云端链接", "").strip()
        if not original_url:
            return ""

        parts = urlsplit(original_url)
        path = parts.path
        if "." not in path.rsplit("/", 1)[-1]:
            return ""

        new_path = path.rsplit(".", 1)[0] + ".md"

        return urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))

    def _extract_lesson_plan_topics(self, text: str) -> List[str]:
        """
        从文件名或目录中提取教案主题关键词
        """
        topic_keywords = [
            '单调性', '奇偶性', '周期性', '对称性', '最值', '最大值', '最小值',
            '概念', '表示法', '性质', '应用', '图像', '图象',
            '幂函数', '指数函数', '对数函数', '三角函数', '二次函数', '一次函数',
            '诱导公式', '三角恒等变换', '零点', '二分法',
            '任意角', '弧度制', '同角三角函数',
            '抛物线', '顶点', '对称轴', '开口',
            '方程', '方程求解', '解方程',
            '实际应用', '生活应用', '数学建模',
            '放射性衰变', '指数增长', '指数衰减',
            '周期性变化', '波形', '正弦', '余弦', '正切',
            '概率', '统计', '抽样', '频率', '分布', '复数', '空间向量', '立体几何'
        ]
        return [keyword for keyword in topic_keywords if keyword in text]

    def _build_lesson_plan_fallback_content(
        self,
        row: Dict[str, str],
        logical_path: str,
        linked_row: Optional[Dict[str, str]],
        extracted_topics: List[str]
    ) -> str:
        """
        当云端Markdown不可用时，用索引元数据构建可检索摘要
        """
        parts = ["教案资源"]

        board = row.get("板块", "").strip()
        if board:
            parts.append(f"板块：{board}")

        directory = row.get("目录", "").strip()
        if directory:
            parts.append(f"目录：{directory}")

        filename = row.get("文件名", "").strip()
        if filename:
            parts.append(f"Markdown文件：{filename}")

        if extracted_topics:
            parts.append(f"知识点：{', '.join(dict.fromkeys(extracted_topics))}")

        if linked_row:
            original_name = linked_row.get("文件名", "").strip()
            original_url = linked_row.get("云端链接", "").strip()
            if original_name:
                parts.append(f"原文件：{original_name}")
            if original_url:
                parts.append(f"原文件链接：{original_url}")

        image_count = row.get("图片数量", "").strip()
        if image_count:
            parts.append(f"图片数量：{image_count}")

        remark = row.get("备注", "").strip()
        if remark:
            parts.append(f"备注：{remark}")

        full_path = row.get("完整路径", "").strip()
        if full_path:
            parts.append(f"完整路径：{full_path}")
        else:
            parts.append(f"逻辑路径：{logical_path}")

        parts.append("说明：云端Markdown正文缺失，当前使用索引摘要参与检索。")
        return "\n".join(parts)

    def _parse_cloud_lesson_plan_tables(self) -> List[Dict[str, str]]:
        """
        基于根目录CSV索引解析云端教案资源
        仅使用Markdown文件建索引，并关联原始文件与图片资源
        """
        index_rows = self._load_cloud_lesson_plan_index()
        if not index_rows:
            return []

        rows_by_filename: Dict[str, Dict[str, str]] = {}
        rows_by_name: Dict[str, List[Dict[str, str]]] = {}
        for row in index_rows:
            logical_path = self._build_logical_lesson_plan_path(row)
            rows_by_filename[logical_path.lower()] = row
            rows_by_name.setdefault(self._normalize_filename_key(row.get("文件名", "")), []).append(row)

        markdown_rows = [
            row for row in index_rows
            if row.get("扩展名", "").lower() == ".md" or row.get("文件类型", "") == "Markdown文件"
        ]

        all_lesson_plans = []
        grade_enricher = get_grade_enricher()

        for row in markdown_rows:
            filename = row.get("文件名", "")
            logical_path = self._build_logical_lesson_plan_path(row)
            title = Path(filename).stem
            directory = row.get("目录", "")
            full_text = f"{title} {directory} {logical_path}"

            chapter_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', full_text)
            chapter = chapter_match.group(1) if chapter_match else ''

            extracted_topics = self._extract_lesson_plan_topics(full_text)
            linked_filename = row.get("关联文件", "").strip()
            linked_row = self._find_linked_lesson_plan_row(row, rows_by_filename, rows_by_name)

            markdown_url = row.get("云端链接", "").strip()
            if not markdown_url:
                markdown_url = self._derive_markdown_url(filename, linked_row)

            content = self._download_cloud_markdown(markdown_url)
            content_source = "cloud_markdown"
            if not content:
                logger.warning(f"云端教案Markdown缺失，使用索引摘要降级: {logical_path}")
                content = self._build_lesson_plan_fallback_content(row, logical_path, linked_row, extracted_topics)
                content_source = "index_fallback"

            item = {
                'resource_type': 'lesson_plan',
                'source_file': logical_path,
                'title': title,
                'content': content,
                '章节': chapter,
                '知识点标签': ', '.join(dict.fromkeys(extracted_topics)),
                '文件名主题': extracted_topics[0] if extracted_topics else '',
                '文件名': filename,
                '目录': directory,
                '云端链接': markdown_url,
                '完整路径': row.get("完整路径", ""),
                '关联文件': linked_filename,
                '原文件云端链接': linked_row.get("云端链接", "") if linked_row else "",
                '原文件名': linked_row.get("文件名", "") if linked_row else linked_filename,
                '图片数量': row.get("图片数量", ""),
                '备注': row.get("备注", ""),
                '板块': row.get("板块", ""),
                '索引文件': row.get("索引文件", ""),
                'content_source': content_source
            }

            grade_enricher.enrich_resource_grade(item)
            all_lesson_plans.append(item)

        if all_lesson_plans:
            grade_stats = grade_enricher.get_grade_statistics(all_lesson_plans)
            logger.info(f"云端教案年级分布: {grade_stats}")

        logger.info(f"解析云端教案资源完成，共{len(all_lesson_plans)}条记录")
        return all_lesson_plans
    
    def _init_keyword_mappings(self):
        """
        V54.0改进：初始化关键词映射表
        动态从资源库中提取常见关键词
        """
        # 函数类型关键词
        self.function_types = [
            "三角函数", "指数函数", "对数函数", "二次函数", "幂函数", 
            "一次函数", "反比例函数", "分段函数", "复合函数"
        ]
        
        # 函数性质关键词
        self.function_properties = [
            "单调性", "奇偶性", "周期性", "最值", "最大值", "最小值",
            "零点", "定义域", "值域", "解析式", "表示法", "概念", "图象", "图像"
        ]
        
        # 数学主题关键词
        self.math_topics = [
            "函数", "方程", "不等式", "数列", "概率", "统计",
            "向量", "立体几何", "解析几何", "导数", "积分",
            "三角恒等变换", "诱导公式", "二倍角公式", "和差化积",
            "数形结合", "分类讨论", "转化与化归", "函数与方程"
        ]
        
        # 教学场景关键词
        self.teaching_scenarios = [
            "新授课", "复习课", "练习课", "讲评课", "实验课",
            "概念课", "定理课", "应用课", "综合课"
        ]
        
        # 年级关键词映射
        self.grade_keywords = {
            "高一": ["必修一", "必修第一册", "第一章", "第二章", "第三章", "第四章", "第五章"],
            "高二": ["必修二", "必修第二册", "选择性必修一", "选择性必修二"],
            "高三": ["高考", "复习", "综合", "模拟", "真题"]
        }
    
    def _extract_keywords_from_text(self, text: str, keyword_list: List[str]) -> List[str]:
        """
        V54.0改进：从文本中提取匹配的关键词
        
        Args:
            text: 待提取的文本
            keyword_list: 关键词列表
            
        Returns:
            匹配到的关键词列表
        """
        matched_keywords = []
        text_lower = text.lower()
        
        for keyword in keyword_list:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)
        
        return matched_keywords
    
    def _enhance_search_text(self, base_text: str, resource_type: str, resource: Dict[str, str]) -> str:
        """
        V54.0改进：增强搜索文本，动态添加相关关键词
        
        Args:
            base_text: 基础搜索文本
            resource_type: 资源类型
            resource: 资源字典
            
        Returns:
            增强后的搜索文本
        """
        enhanced_parts = [base_text]
        
        # 获取资源内容
        content = resource.get('内容', '') or resource.get('教学任务（教学内容）', '') or resource.get('分析', '') or resource.get('题干', '')
        filename = resource.get('文件名', '') or resource.get('视频文件名/网址', '') or resource.get('题目文件名', '')
        chapter = resource.get('章节', '')
        source_file = resource.get('source_file', '')
        
        # 合并所有文本进行分析
        all_text = f"{base_text} {content} {filename} {chapter} {source_file}"
        
        # 动态提取函数类型
        function_types = self._extract_keywords_from_text(all_text, self.function_types)
        for func_type in function_types:
            if func_type not in base_text:
                enhanced_parts.append(func_type)
        
        # 动态提取函数性质
        function_props = self._extract_keywords_from_text(all_text, self.function_properties)
        for prop in function_props:
            # 如果是函数性质，确保包含"函数"前缀
            if prop not in base_text:
                if '函数' not in prop:
                    enhanced_parts.append(f"函数的{prop}")
                else:
                    enhanced_parts.append(prop)
        
        # 动态提取数学主题
        math_topics = self._extract_keywords_from_text(all_text, self.math_topics)
        for topic in math_topics:
            if topic not in base_text:
                enhanced_parts.append(topic)
        
        # 动态提取年级信息
        for grade, keywords in self.grade_keywords.items():
            if any(kw in all_text for kw in keywords):
                if grade not in base_text:
                    enhanced_parts.append(grade)
                break
        
        # 动态提取教学场景
        scenarios = self._extract_keywords_from_text(all_text, self.teaching_scenarios)
        for scenario in scenarios:
            if scenario not in base_text:
                enhanced_parts.append(scenario)
        
        # 去重并返回
        unique_parts = []
        seen = set()
        for part in enhanced_parts:
            if part not in seen:
                unique_parts.append(part)
                seen.add(part)
        
        return '，'.join(unique_parts)
        
    def parse_markdown_table(self, content: str) -> List[Dict[str, str]]:
        """
        解析markdown表格内容
        
        Args:
            content: markdown文件内容
            
        Returns:
            解析后的表格数据，每行是一个字典
        """
        lines = content.strip().split('\n')
        
        # 检查是否是特殊表格格式（使用+和-符号）
        if '+:' in content or '+---' in content:
            return self._parse_special_table(lines)
        
        # 标准markdown表格格式
        return self._parse_standard_table(lines)
    
    def _parse_standard_table(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        解析标准markdown表格（使用|符号）
        
        Args:
            lines: 文件行列表
            
        Returns:
            解析后的表格数据
        """
        # 找到表格开始和结束位置
        table_start = -1
        table_end = -1
        
        for i, line in enumerate(lines):
            # 跳过标题行（以#开头）
            if line.strip().startswith('#'):
                continue
            
            # 检查是否是表格开始行（包含|）
            if '|' in line and table_start == -1:
                table_start = i
            # 检查是否是表格结束行（不包含|且不包含+，且不是空行）
            elif '|' not in line and '+' not in line and table_start != -1:
                # 检查是否是空行（只有空格或完全为空）
                if line.strip() == '':
                    # 空行，继续解析
                    continue
                # 非空行且不包含|或+，表格结束
                table_end = i
                break
        
        if table_start == -1:
            return []
        
        if table_end == -1:
            table_end = len(lines)
        
        # 提取表格行（只包含|的行）
        table_lines = []
        for i in range(table_start, table_end):
            line = lines[i]
            if '|' in line:
                table_lines.append(line)
        
        # 检查是否是Excel导出的表格（第一行是标题，第二行是空白/分隔线，第三行是表头）
        is_excel_table = False
        if len(table_lines) >= 3:
            # 检查文件第一行是否包含".xlsx"（Excel导出的文件通常在第一行有.xlsx文件名）
            # 注意：这里检查的是原始文件的第一行，而不是表格的第一行
            if len(lines) > 0:
                file_first_line = lines[0].strip()
                if '.xlsx' in file_first_line or ('Unnamed' in file_first_line):
                    # 检测到Excel导出的表格
                    is_excel_table = True
        
        # V53.9改进：检测并处理两行表头的情况
        # 如果表格第一行包含"Unnamed"，说明是Excel导出的错误表头，需要跳过
        has_two_headers = False
        if len(table_lines) >= 4:
            first_row = self._parse_table_row(table_lines[0])
            # 检查第一行是否包含"Unnamed"或文件名（如"课件汇总"）
            if any('Unnamed' in cell for cell in first_row) or any('.xlsx' in cell for cell in first_row):
                # 检查第三行是否是实际的列名（不包含Unnamed）
                third_row = self._parse_table_row(table_lines[2])
                if not any('Unnamed' in cell for cell in third_row):
                    has_two_headers = True
                    print(f"   📝 V53.9检测到两行表头，跳过第一行错误表头")
        
        # 如果是Excel导出的表格，跳过原始文件的第2行（Excel导出的文件名），保留表头行
        if is_excel_table:
            # 重新提取表格行，跳过原始文件的第2行
            table_lines = []
            for i in range(table_start, table_end):
                # 跳过第2行（Excel导出的文件名）
                if i == 1:
                    continue
                line = lines[i]
                if '|' in line:
                    table_lines.append(line)
        
        # V53.9改进：如果检测到两行表头，跳过第一行（错误表头）和第二行（分隔线），使用第三行（实际列名）
        if has_two_headers and len(table_lines) >= 4:
            # 跳过第一行（错误表头）和第二行（分隔线），使用第三行作为表头
            header_line = table_lines[2]
            # 数据行从第四行开始
            data_lines = table_lines[3:] if len(table_lines) > 3 else []
            print(f"   📝 V53.9使用第三行作为表头: {header_line[:80]}...")
        else:
            # 解析表头
            header_line = table_lines[0]
            # 跳过分隔线（第二行），数据行从第三行开始
            data_lines = table_lines[1:] if len(table_lines) > 1 else []
        
        headers = self._parse_table_row(header_line)
        
        # 过滤掉分隔线行，并合并多行表格单元格
        filtered_data_lines = []
        for i in range(len(data_lines)):
            line = data_lines[i]
            
            # 检查是否是分隔线（包含:---或类似的模式）
            row = self._parse_table_row(line)
            is_separator = any(':---' in cell or '---' in cell for cell in row)
            if is_separator:
                continue
            
            # 检查这一行是否是表格行的延续（第一列为空）
            if len(row) > 0 and not row[0].strip() and filtered_data_lines:
                # 这是表格行的延续，合并到上一行
                filtered_data_lines[-1] += " " + line.strip()
            else:
                # 这是一个新的表格行
                filtered_data_lines.append(line.strip())
        
        data_lines = filtered_data_lines
        
        # 解析数据行
        data = []
        for line in data_lines:
            row = self._parse_table_row(line)
            
            # 检查是否是分隔线（包含:---或类似的模式）
            is_separator = any(':---' in cell or '---' in cell for cell in row)
            
            # 如果不是分隔线，且列数匹配，则添加到数据中
            if not is_separator:
                # 如果列数不匹配，尝试调整
                if len(row) != len(headers):
                    # 如果列数比表头多，且最后一列为空，则去掉最后一列
                    if len(row) > len(headers) and not row[-1].strip():
                        row = row[:-1]
                    # 如果列数还是不匹配，跳过这一行
                    if len(row) != len(headers):
                        continue
                
                # 如果列数匹配，则添加到数据中
                if len(row) == len(headers):
                    row_dict = {headers[i]: row[i] for i in range(len(headers))}
                    data.append(row_dict)
        
        return data
    
    def _parse_special_table(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        解析特殊表格格式（使用+和|符号）
        
        Args:
            lines: 文件行列表
            
        Returns:
            解析后的表格数据
        """
        # 找到表格开始和结束位置
        table_start = -1
        table_end = -1
        
        for i, line in enumerate(lines):
            # 跳过标题行（以#开头）
            if line.strip().startswith('#'):
                continue
            
            # 检查是否是表格开始行（包含|）
            if '|' in line and table_start == -1:
                table_start = i
            # 检查是否是表格结束行（不包含|且不包含+，且不是空行）
            elif '|' not in line and '+' not in line and table_start != -1:
                # 检查是否是空行（只有空格或完全为空）
                if line.strip() == '':
                    # 空行，继续解析
                    continue
                # 非空行且不包含|或+，表格结束
                table_end = i
                break
        
        if table_start == -1:
            return []
        
        if table_end == -1:
            table_end = len(lines)
        
        # 提取表格行（只包含|的行）
        table_lines = []
        for i in range(table_start, table_end):
            line = lines[i]
            if '|' in line:
                table_lines.append(line)
        
        # 检查是否是Excel导出的表格（第一行是标题，第二行是分隔线，第三行是表头）
        if len(table_lines) >= 3:
            first_line = table_lines[0].strip()
            # 检查第一行是否包含".xlsx"或看起来像Excel标题
            if '.xlsx' in first_line or ('Unnamed' in first_line):
                # 跳过Excel标题行和分隔线，从第三行开始解析
                table_lines = table_lines[2:]
        
        # 解析表头（第一行）
        header_line = table_lines[0]
        headers = self._parse_special_table_row(header_line)
        
        # 跳过分隔线（第二行）
        data_lines = table_lines[1:] if len(table_lines) > 1 else []
        
        # 解析数据行（处理多行单元格）
        data = []
        current_record = {}
        
        for line in data_lines:
            row = self._parse_special_table_row(line)
            
            # 跳过分隔行（只包含-）
            if len(row) > 1 and all(c in '- ' for c in row[1].strip()):
                continue
            
            # 检查是否是新的记录行（第一列不为空）
            if len(row) > 0 and row[0].strip():
                # 保存上一条记录
                if current_record:
                    data.append(current_record)
                
                # 开始新记录
                if len(row) == len(headers):
                    current_record = {headers[i]: row[i] for i in range(len(headers))}
            # 检查是否是续行（第一列为空，第二列不为空）
            elif len(row) > 1 and not row[0].strip() and row[1].strip():
                if current_record and len(headers) > 1:
                    current_record[headers[1]] += "\n" + row[1].strip()
        
        # 保存最后一条记录
        if current_record:
            data.append(current_record)
        
        return data
    
    def _parse_special_table_row(self, line: str) -> List[str]:
        """
        解析特殊表格行（使用|作为分隔符）
        
        Args:
            line: 表格行内容
            
        Returns:
            解析后的单元格列表
        """
        # 移除首尾的|
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        
        # 分割单元格（使用|作为分隔符）
        cells = [cell.strip() for cell in line.split('|')]
        return cells
    
    def _parse_space_separated_table(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        解析空格分隔的表格
        
        Args:
            lines: 文件行列表
            
        Returns:
            解析后的表格数据
        """
        # 找到表格开始和结束位置
        table_start = -1
        table_end = -1
        
        for i, line in enumerate(lines):
            # 跳过标题行（以#开头）
            if line.strip().startswith('#'):
                continue
            
            # 检查是否是分隔线（只包含-和空格）
            if line.strip().startswith('-') and all(c in '- ' for c in line.strip()):
                # 分隔线的下一行应该是表头
                if i + 1 < len(lines) and table_start == -1:
                    table_start = i + 1
            # 检查是否是表格结束行（新标题）
            elif line.strip().startswith('#') and table_start != -1:
                table_end = i
                break
        
        if table_start == -1:
            return []
        
        if table_end == -1:
            table_end = len(lines)
        
        # 提取表格行
        table_lines = lines[table_start:table_end]
        
        # 解析表头（第一行）
        header_line = table_lines[0].strip()
        headers = [h.strip() for h in header_line.split()]
        
        # 跳过分隔线（第二行）
        data_lines = table_lines[2:] if len(table_lines) > 2 else []
        
        # 解析数据行
        data = []
        current_record = {}
        
        for line in data_lines:
            line = line.strip()
            
            # 跳过空行和分隔线
            if not line or (line.startswith('-') and all(c in '- ' for c in line)):
                continue
            
            # 检查是否是章节行（以数字开头，如"3.1"）
            if re.match(r'^\d+\.\d+', line):
                # 保存上一条记录
                if current_record:
                    data.append(current_record)
                
                # 开始新记录
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    current_record = {
                        '章节': parts[0],
                        '教学任务（教学内容）': parts[1]
                    }
                else:
                    current_record = {
                        '章节': parts[0],
                        '教学任务（教学内容）': ''
                    }
            # 检查是否是任务行（以①、②等开头）
            elif re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', line):
                if current_record:
                    current_record['教学任务（教学内容）'] += "\n" + line
        
        # 保存最后一条记录
        if current_record:
            data.append(current_record)
        
        return data
    
    def _parse_table_row(self, line: str) -> List[str]:
        """
        解析表格行
        
        Args:
            line: 表格行内容
            
        Returns:
            解析后的单元格列表
        """
        # 移除首尾的|
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        
        # 分割单元格
        cells = [cell.strip() for cell in line.split('|')]
        return cells
    
    def parse_ggb_table(self) -> List[Dict[str, str]]:
        """
        解析GGB资源汇总表
        支持.md和.xlsx格式
        
        Returns:
            GGB资源列表
        """
        # 首先尝试查找.md文件
        ggb_file = self.learning_resource_path / 'ggb' / 'ggb信息.md'
        
        if ggb_file.exists():
            # 解析markdown文件
            with open(ggb_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            data = self.parse_markdown_table(content)
            
            # 添加资源类型
            for item in data:
                item['resource_type'] = 'ggb'
            
            logger.info(f"解析GGB汇总表(md)，共{len(data)}条记录")
            return data
        
        # 如果没有.md文件，尝试.xlsx文件
        ggb_xlsx = self.learning_resource_path / 'ggb' / 'ggb信息.xlsx'
        
        if ggb_xlsx.exists():
            try:
                import pandas as pd
                
                # 读取Excel文件
                df = pd.read_excel(ggb_xlsx)
                
                # 转换为字典列表
                data = []
                i = 1
                for _, row in df.iterrows():
                    # 为GGB资源创建有效的标题
                    title_parts = []
                    if pd.notna(row.get('章节')) and row['章节'].strip():
                        title_parts.append(row['章节'].strip())
                    if pd.notna(row.get('ggb文件名')) and row['ggb文件名'].strip():
                        title_parts.append(row['ggb文件名'].strip())
                    if pd.notna(row.get('教学用途')) and row['教学用途'].strip():
                        title_parts.append(row['教学用途'].strip())
                    
                    title = ' - '.join(title_parts) if title_parts else f"GGB资源_{i}"
                    
                    item = {
                        'resource_type': 'ggb',
                        'source_file': str(ggb_xlsx.relative_to(self.learning_resource_path)),
                        'title': title,
                        **{k: str(v) if pd.notna(v) else '' for k, v in row.items()}
                    }
                    data.append(item)
                    i += 1
                
                logger.info(f"解析GGB汇总表(xlsx)，共{len(data)}条记录")
                return data
                
            except Exception as e:
                logger.error(f"解析GGB Excel文件失败: {e}")
                return []
        
        logger.warning(f"GGB汇总表不存在: {ggb_file} 或 {ggb_xlsx}")
        return []
    
    def parse_syllabus_table(self) -> List[Dict[str, str]]:
        """
        解析教学大纲汇总表
        
        Returns:
            教学大纲资源列表
        """
        syllabus_file = self.learning_resource_path / '教学大纲' / '函数教学大纲.md'
        
        if not syllabus_file.exists():
            logger.warning(f"教学大纲汇总表不存在: {syllabus_file}")
            return []
        
        with open(syllabus_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析所有表格
        all_data = []
        
        # 先尝试标准表格格式（使用|符号）
        standard_data = self.parse_markdown_table(content)
        all_data.extend(standard_data)
        
        # 尝试解析特殊表格格式（使用+和|符号）
        lines = content.split('\n')
        special_data = self._parse_special_table(lines)
        all_data.extend(special_data)
        
        # 尝试解析空格分隔的表格
        space_data = self._parse_space_separated_table(lines)
        all_data.extend(space_data)
        
        # 如果没有找到任何表格，尝试解析包含章节和教学任务的行
        if not standard_data and not special_data and not space_data:
            current_chapter = ""
            current_task = ""
            
            for line in lines:
                line = line.strip()
                
                # 跳过空行和标题
                if not line or line.startswith('#'):
                    continue
                
                # 检查是否是章节行（以数字开头，如"3.1"）
                if re.match(r'^\d+\.\d+', line):
                    # 保存上一条记录
                    if current_chapter and current_task:
                        all_data.append({
                            '章节': current_chapter,
                            '教学任务（教学内容）': current_task
                        })
                    
                    # 开始新记录
                    current_chapter = line.split()[0]  # 提取章节号
                    current_task = line
                
                # 检查是否是任务行（以①、②等开头）
                elif re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', line):
                    current_task += "\n" + line
            
            # 保存最后一条记录
            if current_chapter and current_task:
                all_data.append({
                    '章节': current_chapter,
                    '教学任务（教学内容）': current_task
                })
        
        # 添加资源类型、源文件路径和标题
        for i, item in enumerate(all_data):
            item['resource_type'] = 'syllabus'
            item['source_file'] = str(syllabus_file.relative_to(self.learning_resource_path))
            # 为教学大纲资源创建标题
            chapter = item.get('章节', '')
            task = item.get('教学任务（教学内容）', '')
            title = f"{chapter} - {task[:30]}" if task else f"{chapter}" if chapter else f"教学大纲资源_{i+1}"
            item['title'] = title
        
        logger.info(f"解析教学大纲汇总表，共{len(all_data)}条记录")
        return all_data
    
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
    
    def parse_lesson_plan_tables(self) -> List[Dict[str, str]]:
        """
        解析教案资源汇总表
        改进：从文件名和文件路径中提取章节和主题信息
        
        Returns:
            教案资源列表
        """
        cloud_lesson_plans = self._parse_cloud_lesson_plan_tables()
        if cloud_lesson_plans:
            return cloud_lesson_plans

        lesson_plan_folder = self.learning_resource_path / '教案'
        
        if not lesson_plan_folder.exists():
            logger.warning(f"教案文件夹不存在: {lesson_plan_folder}")
            return []
        
        all_lesson_plans = []
        
        # 遍历教案文件夹中的所有.md文件
        for md_file in lesson_plan_folder.rglob('*.md'):
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
                
                logger.info(f"解析教案: {md_file.name}, 章节: {chapter}, 主题: {knowledge_tags}, 年级: {item.get('grade', '未知')}")
                
            except Exception as e:
                logger.error(f"解析教案文件失败: {md_file}, 错误: {e}")
        
        # V12.0改进2：记录年级分布统计
        if all_lesson_plans:
            grade_stats = get_grade_enricher().get_grade_statistics(all_lesson_plans)
            logger.info(f"教案年级分布: {grade_stats}")
        
        logger.info(f"解析教案汇总表完成，共{len(all_lesson_plans)}条记录")
        return all_lesson_plans
    
    def parse_theory_cards(self) -> List[Dict[str, str]]:
        """
        解析理论卡片
        
        Returns:
            理论卡片列表
        """
        theory_cards = []
        
        # 在理论卡片文件夹中查找理论卡片
        theory_folder = self.learning_resource_path / '理论卡片'
        
        if theory_folder.exists():
            for md_file in theory_folder.rglob('*.md'):
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    item = {
                        'resource_type': 'theory',
                        'source_file': str(md_file.relative_to(self.learning_resource_path)),
                        'title': md_file.stem,
                        'content': content
                    }
                    theory_cards.append(item)
                    
                    logger.info(f"解析理论卡片: {md_file.name}")
                    
                except Exception as e:
                    logger.error(f"解析理论卡片失败: {md_file}, 错误: {e}")
        
        # 在教案文件夹中查找理论卡片（向后兼容）
        lesson_plan_folder = self.learning_resource_path / '教案'
        
        if lesson_plan_folder.exists():
            for md_file in lesson_plan_folder.rglob('*.md'):
                if '理论卡片' in md_file.name:
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        item = {
                            'resource_type': 'theory',
                            'source_file': str(md_file.relative_to(self.learning_resource_path)),
                            'title': md_file.stem,
                            'content': content
                        }
                        theory_cards.append(item)
                        
                        logger.info(f"解析理论卡片: {md_file.name}")
                        
                    except Exception as e:
                        logger.error(f"解析理论卡片失败: {md_file}, 错误: {e}")
        
        # 解析优秀教案共性整合文档
        theory_file = lesson_plan_folder / '优秀教案共性整合（最终版）.md'
        if theory_file.exists():
            try:
                with open(theory_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                item = {
                    'resource_type': 'theory',
                    'source_file': str(theory_file.relative_to(self.learning_resource_path)),
                    'title': theory_file.stem,
                    'content': content
                }
                theory_cards.append(item)
                
                logger.info(f"解析优秀教案共性整合文档")
                
            except Exception as e:
                logger.error(f"解析优秀教案共性整合文档失败: {e}")
        
        logger.info(f"解析理论卡片完成，共{len(theory_cards)}条记录")
        return theory_cards
    
    def parse_courseware_table(self) -> List[Dict[str, str]]:
        """
        解析课件资源汇总表
        
        Returns:
            课件资源列表
        """
        courseware_folder = self.learning_resource_path / '课件'
        
        if not courseware_folder.exists():
            logger.warning(f"课件文件夹不存在: {courseware_folder}")
            return []
        
        all_courseware = []
        
        # 遍历课件文件夹中的所有.md文件
        for md_file in courseware_folder.rglob('*.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                data = self.parse_markdown_table(content)
                
                # 添加资源类型、文件路径和标题
                for i, item in enumerate(data):
                    item['resource_type'] = 'courseware'
                    item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                    # 为课件资源创建标题
                    content = item.get('内容', '')
                    filename = item.get('文件名', '')
                    title_parts = []
                    if filename:
                        title_parts.append(filename)
                    if content:
                        title_parts.append(content[:20])
                    title = ' - '.join(title_parts) if title_parts else f"课件资源_{i+1}"
                    item['title'] = title
                
                all_courseware.extend(data)
                logger.info(f"解析课件汇总表: {md_file.name}, 共{len(data)}条记录")
                
            except Exception as e:
                logger.error(f"解析课件文件失败: {md_file}, 错误: {e}")
        
        # 遍历课件文件夹中的所有.xlsx文件
        for xlsx_file in courseware_folder.rglob('*.xlsx'):
            try:
                import pandas as pd
                
                df = pd.read_excel(xlsx_file)
                data = []
                
                # 遍历DataFrame的每一行
                for i, row in df.iterrows():
                    item = {}
                    # 遍历每一列
                    for col in df.columns:
                        if pd.notna(row[col]):
                            item[col] = str(row[col])
                        else:
                            item[col] = ''
                    
                    # 添加资源类型、文件路径和标题
                    item['resource_type'] = 'courseware'
                    item['source_file'] = str(xlsx_file.relative_to(self.learning_resource_path))
                    # 为课件资源创建标题
                    content = item.get('内容', '')
                    filename = item.get('文件名', '')
                    title_parts = []
                    if filename:
                        title_parts.append(filename)
                    if content:
                        title_parts.append(content[:20])
                    title = ' - '.join(title_parts) if title_parts else f"课件资源_{i+1}"
                    item['title'] = title
                    
                    data.append(item)
                
                all_courseware.extend(data)
                logger.info(f"解析课件汇总表(xlsx): {xlsx_file.name}, 共{len(data)}条记录")
                
            except Exception as e:
                logger.error(f"解析课件文件失败: {xlsx_file}, 错误: {e}")
        
        logger.info(f"解析课件汇总表完成，共{len(all_courseware)}条记录")
        return all_courseware
    
    def parse_lesson_case_table(self) -> List[Dict[str, str]]:
        """
        解析课例资源汇总表
        
        Returns:
            课例资源列表
        """
        lesson_case_folder = self.learning_resource_path / '课例视频'
        
        if not lesson_case_folder.exists():
            logger.warning(f"课例视频文件夹不存在: {lesson_case_folder}")
            return []
        
        all_lesson_cases = []
        
        # 遍历课例视频文件夹中的所有.md文件
        for md_file in lesson_case_folder.rglob('*.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                data = self.parse_markdown_table(content)
                
                # 添加资源类型、文件路径和标题
                for i, item in enumerate(data):
                    item['resource_type'] = 'lesson_case'
                    item['source_file'] = str(md_file.relative_to(self.learning_resource_path))
                    # 为课例资源创建标题
                    chapter = item.get('章节', '')
                    filename = item.get('视频文件名/网址', '')
                    analysis = item.get('分析', '')
                    title_parts = []
                    if chapter:
                        title_parts.append(chapter)
                    if filename and not filename.startswith('http'):
                        title_parts.append(filename)
                    if analysis:
                        title_parts.append(analysis[:20])
                    title = ' - '.join(title_parts) if title_parts else f"课例资源_{i+1}"
                    item['title'] = title
                
                all_lesson_cases.extend(data)
                logger.info(f"解析课例视频汇总表: {md_file.name}, 共{len(data)}条记录")
                
            except Exception as e:
                logger.error(f"解析课例视频文件失败: {md_file}, 错误: {e}")
        
        logger.info(f"解析课例视频汇总表完成，共{len(all_lesson_cases)}条记录")
        return all_lesson_cases
    
    def parse_all_tables(self) -> Dict[str, List[Dict[str, str]]]:
        """
        解析所有资源汇总表
        
        Returns:
            所有资源的字典，按类型分组
        """
        logger.info("开始解析所有资源汇总表...")
        
        all_resources = {
            'ggb': self.parse_ggb_table(),
            'syllabus': self.parse_syllabus_table(),
            'exercise': self.parse_exercise_tables(),
            'lesson_plan': self.parse_lesson_plan_tables(),
            'theory': self.parse_theory_cards(),
            'courseware': self.parse_courseware_table(),
            'lesson_case': self.parse_lesson_case_table()
        }
        
        total_count = sum(len(resources) for resources in all_resources.values())
        logger.info(f"解析完成，共{total_count}条记录")
        
        return all_resources
    
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
    
    def _extract_topic_from_filename(self, filename: str) -> str:
        """
        从课例文件名中提取知识点信息
        
        Args:
            filename: 文件名，如 "4.2.1指数函数的概念.mp4"
            
        Returns:
            提取的知识点信息
        """
        # 移除文件扩展名
        name = Path(filename).stem
        
        # 移除常见的标记
        name = re.sub(r'【.*?】', '', name)  # 移除【单调性】等标记
        name = re.sub(r'\(.*?\)', '', name)  # 移除括号内容
        name = re.sub(r'\（.*?\）', '', name)  # 移除中文括号内容
        
        # 提取数字编号后的内容（如 "4.2.1指数函数的概念" -> "指数函数的概念"）
        match = re.search(r'^[\d\.]+\s*(.+)$', name)
        if match:
            return match.group(1).strip()
        
        # 如果没有数字编号，直接返回文件名
        return name
    
    def get_resource_filename(self, resource: Dict[str, str]) -> Optional[str]:
        """
        获取资源的文件名
        
        Args:
            resource: 资源字典
            
        Returns:
            文件名，如果没有则返回None
        """
        resource_type = resource.get('resource_type', '')
        
        if resource_type == 'ggb':
            return resource.get('ggb文件名')
        
        elif resource_type == 'exercise':
            return resource.get('题目文件名')
        
        elif resource_type in ['lesson_plan', 'theory']:
            return resource.get('原文件云端链接') or resource.get('云端链接') or resource.get('source_file')
        
        elif resource_type == 'courseware':
            return resource.get('文件名')
        
        elif resource_type == 'lesson_case':
            return resource.get('视频文件名/网址')
        
        return None
