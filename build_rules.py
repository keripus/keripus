import os

SRC_DIR = './v2fly_src/data'
OUTPUT_DIR = 'rule/surge'


def clean_line(line: str) -> str:
    """
    步骤 2：单行语法清洗器
    专门剥离 v2fly 各种高级语法标签（full:, @!cn 等），提炼出 Surge 认识的纯域名
    """
    # 砍掉尾部的 @!cn, :@ads 等属性旗标，只拿第一段
    main_part = line.split()[0].strip()
    
    # 剥离 full: 前缀
    if main_part.startswith('full:'):
        clean_domain = main_part.replace('full:', '', 1).split(':')[0].strip()
    else:
        clean_domain = main_part.split(':')[0].strip()
        
    # 如果清洗后符合域名基本特征且不是特殊控制符，则返回，否则返回空字符串
    return clean_domain if not clean_domain.startswith('@') else ""


def load_source_file(file_name: str) -> list:
    """
    步骤 3：单文件数据加载器
    负责物理读取，并过滤掉基础的空行与注释
    """
    file_path = os.path.join(SRC_DIR, file_name)
    if not os.path.exists(file_path):
        return []

    valid_lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 过滤掉空行和纯注释行
                if line and not line.startswith('#'):
                    valid_lines.append(line)
    except Exception as e:
        print(f"⚠️ 读取文件失败 {file_name}: {e}")
        
    return valid_lines


def parse_file(file_name: str, visited: set) -> set:
    """
    步骤 1：核心转译路由器
    采用深度优先搜索 (DFS)，专门处理 include: 嵌套关系，同时通过 visited 沙盒严防死循环
    """
    if file_name in visited:
        return set()
    visited.add(file_name)

    domains = set()
    lines = load_source_file(file_name)

    for line in lines:
        # 情况 A：发现嵌套引入，触发递归
        if line.startswith('include:'):
            inc_file = line.split(':')[1].strip()
            domains.update(parse_file(inc_file, visited))
            continue
        
        # 情况 B：发现 Surge 无法识别的特异性语义，直接跳过
        if line.startswith('keyword:') or line.startswith('regex:') or line.startswith('regexp:'):
            continue

        # 情况 C：标准数据行，送去清洗
        clean_domain = clean_line(line)
        if clean_domain:
            domains.add(clean_domain)
            
    return domains


def main():
    """
    步骤 4：工厂跑批总指挥
    控制全量扫描、调用编译器并最终格式化输出到磁盘
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(SRC_DIR):
        print("❌ 错误：未找到上游源码目录，请检查 git clone 是否成功。")
        return

    all_sources = [f for f in os.listdir(SRC_DIR) if os.path.isfile(os.path.join(SRC_DIR, f))]
    print(f"🚀 侦测到上游共包含 {len(all_sources)} 个规则源文件，开始全量提炼...")
    
    success_count = 0
    for src_file in all_sources:
        # 每个顶级域名集在起跑时，强制初始化独立的防死循环沙盒
        local_visited = set()
        final_set = parse_file(src_file, local_visited)
        
        # 仅在包含有效域名时落盘，防止生成无意义的空文本
        if final_set:
            target_file_name = f"{src_file}.txt"
            full_output_path = os.path.join(OUTPUT_DIR, target_file_name)
            
            with open(full_output_path, 'w', encoding='utf-8') as out:
                out.write('\n'.join(sorted(list(final_set))))
            success_count += 1
            
    print(f"🏁 全量转译大获全胜！成功在 {OUTPUT_DIR} 下生成了 {success_count} 个专属 Surge 文本规则集！")


if __name__ == '__main__':
    main()
