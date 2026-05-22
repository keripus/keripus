import os

SRC_DIR = './v2fly_src/data'
OUTPUT_DIR = 'rule/surge'

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

    try:
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
                
                # 剥离 full: 前缀，留下后面的纯域名
                if main_part.startswith('full:'):
                    clean_domain = main_part.replace('full:', '', 1).split(':')[0].strip()
                else:
                    clean_domain = main_part.split(':')[0].strip()
                
                # 确保符合域名基本特征才录入
                if clean_domain and not clean_domain.startswith('@'):
                    domains.add(clean_domain)
    except Exception as e:
        print(f"⚠️ 读取文件错误 {file_name}: {e}")
                
    return domains

# 创建深层收纳目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🎯 核心黑科技：自动扫描整个 data 目录下的所有规则源文件
if os.path.exists(SRC_DIR):
    all_sources = [f for f in os.listdir(SRC_DIR) if os.path.isfile(os.path.join(SRC_DIR, f))]
    print(f"🚀 侦测到上游共包含 {len(all_sources)} 个规则源文件，开始全量提炼...")
    
    success_count = 0
    for src_file in all_sources:
        # 执行 DFS 递归提纯
        final_set = parse_file(src_file)
        
        # 💡 只有当清洗后里面确实包含合法域名时，才输出文件，防止生成无意义空文本
        if final_set:
            target_file_name = f"{src_file}.txt"
            full_output_path = os.path.join(OUTPUT_DIR, target_file_name)
            
            with open(full_output_path, 'w', encoding='utf-8') as out:
                out.write('\n'.join(sorted(list(final_set))))
            success_count += 1
            
    print(f"🏁 全量转译大获全胜！成功在 {OUTPUT_DIR} 下生成了 {success_count} 个专属 Surge 文本规则集！")
else:
    print("❌ 错误：未找到上游源码目录，请检查 git clone 是否成功。")
