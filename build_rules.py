import os

SRC_DIR = './v2fly_src/data'
OUTPUTS = {
    'youtube.txt': ['youtube'],
    'netflix.txt': ['netflix'],
    'openai.txt': ['openai'],
    'telegram.txt': ['telegram'],
    'proxy.txt': ['geolocation-!cn'],
    'cn.txt': ['cn']
}

def parse_file(file_name, visited=None):
    if visited is None:
        visited = set()
    
    # 防止循环嵌套死循环
    if file_name in visited:
        return set()
    visited.add(file_name)

    domains = set()
    file_path = os.path.join(SRC_DIR, file_name)
    if not os.path.exists(file_path):
        return domains

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 1. 过滤掉空行和注释行
            if not line or line.startswith('#'):
                continue
            
            # 2. 递归处理 include: 嵌套
            if line.startswith('include:'):
                inc_file = line.split(':')[1].strip()
                domains.update(parse_file(inc_file, visited))
                continue
            
            # 3. 过滤掉 Surge 无法识别的 keyword: 和 regex:
            if line.startswith('keyword:') or line.startswith('regex:'):
                continue

            # 4. 洗掉 v2fly 特有的各种后置修饰尾缀
            main_part = line.split()[0].strip()
            
            # 💡剥离 full: 前缀，留下后面的纯域名
            if main_part.startswith('full:'):
                clean_domain = main_part.replace('full:', '', 1).split(':')[0].strip()
            else:
                clean_domain = main_part.split(':')[0].strip()
            
            # 确保符合域名基本特征才录入
            if clean_domain and not clean_domain.startswith('@'):
                domains.add(clean_domain)
                
    return domains

# 创建深层收纳目录
os.makedirs('rule/surge', exist_ok=True)

# 批量开始组装生产线
for target_file, source_files in OUTPUTS.items():
    final_set = set()
    for src in source_files:
        final_set.update(parse_file(src))
    
    # 排序后写入，方便 Git 追踪文本差异
    full_output_path = os.path.join('rule/surge', target_file)
    with open(full_output_path, 'w', encoding='utf-8') as out:
        out.write('\n'.join(sorted(list(final_set))))
    print(f"✅ 成功生成完美 Surge Domain-Set: {full_output_path}, 包含 {len(final_set)} 条唯一域名。")
