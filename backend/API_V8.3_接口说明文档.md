# 资源检索接口说明文档（V8.3版本）

## 概述

V8.3版本对资源检索接口进行了以下改进：
1. **资源分布平衡**：确保多主题查询时每个主题都有合理数量的核心匹配资源
2. **隐藏资源支持**：返回隐藏资源的元数据，支持前端实现"加载更多"功能

## 返回数据结构

### 基础结构

```typescript
interface ResourceSearchResult {
  // 资源分类
  theory_resources: Resource[];
  lesson_plan_patterns: Resource[];
  exercise_resources: Resource[];
  visualization_examples: Resource[];
  general_resources: Resource[];
  courseware_resources: Resource[];
  lesson_case_resources: Resource[];
  ggb_resources: Resource[];
  syllabus_resources: Resource[];
  
  // V8.3新增：隐藏资源信息
  _hidden_resources: Resource[];  // 隐藏的资源列表
  _hidden_count: number;          // 隐藏资源的数量
  _total_count: number;           // 总资源数量（可见+隐藏）
}
```

### Resource对象结构

```typescript
interface Resource {
  title: string;                    // 资源标题
  content: string;                  // 资源内容
  source: string;                   // 文件路径
  relevance: number;                // 相关性分数 (0-1)
  base_relevance: number;            // 基础相关性分数
  theme_match: boolean;              // 是否匹配主题
  type_match: boolean;              // 是否匹配资源类型
  matched_theme_count: number;       // 匹配的主题数量
  theme_boost: number;              // 主题匹配质量提升
  conflict_theme: boolean;           // 是否有主题冲突
  matched_themes: string[];         // 匹配的主题列表
  is_comprehensive: boolean;         // 是否为综合性资源
  core_theme: string;               // 核心主题
  related_themes: string[];         // 相关主题
  mentioned_themes: string[];       // 提及主题
  is_core_match: boolean;           // 是否为核心主题匹配
  match_level: string;              // 匹配级别: 'core' | 'related' | 'mentioned' | 'none'
  domain: string;                  // 领域分类
  explanation: string;             // 匹配说明
  should_show: boolean;            // 是否应该显示
  display_level: string;           // 展示级别
  overall_score: number;            // 综合得分 (0-1)
  resource_quality: number;         // 资源质量 (0-1)
  content_completeness: number;     // 内容完整性 (0-1)
  teaching_value: number;           // 教学价值 (0-1)
  comprehensiveness: number;        // 综合性 (0-1)
  concept_hierarchy_factor: number;   // 概念层级因子 (0-1)
  _category: string;               // 原始分类
}
```

## 前端需要实现的功能

### 1. 显示隐藏资源提示

在搜索结果底部显示隐藏资源的信息：

```typescript
// 示例代码
const hiddenCount = result._hidden_count || 0;
const totalCount = result._total_count || 0;

if (hiddenCount > 0) {
  return (
    <div className="hidden-resources-hint">
      <span>💡 已隐藏 {hiddenCount} 条相似度较低的资源</span>
      <span>（共 {totalCount} 条结果）</span>
    </div>
  );
}
```

### 2. 实现"加载更多"功能

提供按钮让用户加载隐藏的资源：

```typescript
// 示例代码
const [showHidden, setShowHidden] = useState(false);

const handleLoadMore = () => {
  setShowHidden(true);
};

// 在渲染时
{!showHidden && hiddenCount > 0 && (
  <button onClick={handleLoadMore} className="load-more-button">
    📂 加载更多资源 ({hiddenCount} 条)
  </button>
)}

{showHidden && hiddenResources.length > 0 && (
  <div className="hidden-resources-section">
    <h3>📂 更多资源</h3>
    {hiddenResources.map((resource, index) => (
      <ResourceCard key={index} resource={resource} />
    ))}
  </div>
)}
```

### 3. 分页加载隐藏资源（可选）

如果隐藏资源数量很多，可以实现分页加载：

```typescript
// 示例代码
const [hiddenPage, setHiddenPage] = useState(1);
const HIDDEN_PAGE_SIZE = 10;

const loadMoreHidden = () => {
  setHiddenPage(prev => prev + 1);
};

const getVisibleHiddenResources = () => {
  return hiddenResources.slice(0, hiddenPage * HIDDEN_PAGE_SIZE);
};

// 在渲染时
{showHidden && (
  <>
    {getVisibleHiddenResources().map((resource, index) => (
      <ResourceCard key={index} resource={resource} />
    ))}
    
    {getVisibleHiddenResources().length < hiddenResources.length && (
      <button onClick={loadMoreHidden} className="load-more-button">
        加载更多 ({hiddenResources.length - getVisibleHiddenResources().length} 条)
      </button>
    )}
  </>
)}
```

### 4. 资源分布平衡说明（可选）

如果需要向用户说明资源分布平衡的逻辑：

```typescript
// 示例代码
const getThemeDistribution = () => {
  const themeCounts = {};
  allResources.forEach(resource => {
    resource.matched_themes.forEach(theme => {
      themeCounts[theme] = (themeCounts[theme] || 0) + 1;
    });
  });
  return themeCounts;
};

// 在渲染时
<div className="theme-distribution">
  <h4>📊 资源分布</h4>
  {Object.entries(getThemeDistribution()).map(([theme, count]) => (
    <span key={theme}>
      {theme}: {count}个
    </span>
  ))}
</div>
```

## 后端日志说明

后端会输出以下日志信息，方便调试：

```
🔄 多主题资源分布平衡，主题: ['三角函数', '幂函数', '对数函数']
📊 各主题资源数量: {'三角函数': 58, '幂函数': 14, '对数函数': 29}
🎯 每个主题目标数量: 15
✅ 主题 '三角函数': 选择 15/58 个资源
✅ 主题 '幂函数': 选择 14/14 个资源
✅ 主题 '对数函数': 选择 15/29 个资源
✅ 平衡完成: 44 个资源（其他资源: 0个）
✅ V8.3排序完成：核心主题优先，共44个可见资源（隐藏83个，总计127个）
```

## 注意事项

1. **向后兼容性**：新增的字段以 `_` 开头，不会影响现有代码
2. **性能考虑**：隐藏资源可能数量较多，建议使用分页加载
3. **用户体验**：建议在显示隐藏资源时提供视觉区分（如灰色背景、降低透明度等）
4. **错误处理**：如果 `_hidden_resources` 字段不存在，说明使用的是旧版本后端，需要做兼容处理

## 示例响应

```json
{
  "theory_resources": [],
  "lesson_plan_patterns": [
    {
      "title": "3.3 幂函数 教学设计（1）",
      "content": "...",
      "source": "教案\\第三章函数的概念与性质\\3.3幂函数\\3.3 幂函数 教学设计（1）.md",
      "relevance": 0.9,
      "matched_themes": ["幂函数"],
      "match_level": "core",
      "overall_score": 0.97,
      "resource_quality": 0.4,
      "content_completeness": 0.1,
      "teaching_value": 0.15,
      "comprehensiveness": 0.2,
      "_category": "lesson_plan_patterns"
    }
    // ... 更多资源
  ],
  "exercise_resources": [],
  "visualization_examples": [],
  "general_resources": [],
  "courseware_resources": [],
  "lesson_case_resources": [],
  "ggb_resources": [],
  "syllabus_resources": [],
  "_hidden_resources": [
    // 隐藏的资源列表
  ],
  "_hidden_count": 83,
  "_total_count": 127
}
```

## 版本信息

- **版本**: V8.3
- **更新日期**: 2026-03-07
- **主要改进**: 资源分布平衡、隐藏资源支持