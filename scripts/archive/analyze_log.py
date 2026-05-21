"""分析日志，按查询变体分组习题结果"""
log_lines = open(r'D:\Git_Repository\Mathemist\终端运行结果.txt', 'r', encoding='utf-8').readlines()

queries = {}  # query_id -> {'debug': [], 'hidden': [], 'result': ''}

current_query = None
for line in log_lines:
    line = line.rstrip('\n')
    if '简化检索完成' in line:
        # 提取主题
        import re
        m = re.search(r"主题='([^']+)'", line)
        if m:
            current_query = m.group(1)
            queries[current_query] = {'debug': [], 'hidden': [], 'result': ''}
    if current_query:
        if '[方案A-调试]' in line:
            queries[current_query]['debug'].append(line)
        elif '[方案A] 隐藏习题' in line:
            queries[current_query]['hidden'].append(line)
        elif '[方案A] 习题返回' in line:
            queries[current_query]['result'] = line

for q, data in queries.items():
    print(f"\n{'='*60}")
    print(f"查询: {q}")
    print(f"结果: {data['result']}")
    print(f"调试日志 ({len(data['debug'])}条):")
    for d in data['debug']:
        m = re.search(r"title='([^']+)'", d)
        title = m.group(1) if m else '?'
        m2 = re.search(r"kp_final='([^']+)'", d)
        kp = m2.group(1) if m2 else '?'
        m3 = re.search(r"relevance=([\d.]+)", d)
        rel = m3.group(1) if m3 else '?'
        # 检查是否被隐藏
        is_hidden = any(title in h for h in data['hidden'])
        status = '隐藏' if is_hidden else '展示'
        print(f"  [{status}] {title} | kp={kp} | rel={rel}")
    print(f"隐藏日志 ({len(data['hidden'])}条):")
    for h in data['hidden']:
        m = re.search(r"title='([^']+)'", h)
        print(f"  {m.group(1) if m else '?'}")
