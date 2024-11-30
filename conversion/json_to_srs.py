import json
import os
from datetime import datetime

def convert_json_to_srs(json_file, srs_file):
    try:
        # 读取 JSON 文件
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rules = []
        # 添加时间戳注释
        rules.append(f"# Rules - Updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        rules.append("")
        
        # 处理规则
        if isinstance(data, dict):
            # 处理 sing-box_ai.json 格式
            if 'rules' in data:
                for rule in data['rules']:
                    if 'domain' in rule:
                        for domain in rule['domain']:
                            rules.append(f"DOMAIN,{domain}")
                    if 'domain_suffix' in rule:
                        for suffix in set(rule['domain_suffix']):  # 使用set去重
                            rules.append(f"DOMAIN-SUFFIX,{suffix}")
                    if 'domain_keyword' in rule:
                        if isinstance(rule['domain_keyword'], str):
                            rules.append(f"DOMAIN-KEYWORD,{rule['domain_keyword']}")
                        elif isinstance(rule['domain_keyword'], list):
                            for keyword in rule['domain_keyword']:
                                rules.append(f"DOMAIN-KEYWORD,{keyword}")
        
        elif isinstance(data, list):
            # 处理 No_HK.json 格式
            for item in data:
                if 'domain' in item:
                    rules.append(f"DOMAIN,{item['domain']}")
                elif 'domain_suffix' in item:
                    rules.append(f"DOMAIN-SUFFIX,{item['domain_suffix']}")
                elif 'domain_keyword' in item:
                    rules.append(f"DOMAIN-KEYWORD,{item['domain_keyword']}")
        
        # 写入 .srs 文件
        os.makedirs(os.path.dirname(srs_file), exist_ok=True)
        with open(srs_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(rules))
        
        print(f"Successfully converted {json_file} to {srs_file}")
        return True
    
    except Exception as e:
        print(f"Error converting file {json_file}: {str(e)}")
        return False

def main():
    # 设置文件路径
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rules_dir = os.path.join(current_dir, 'rules')
    
    # 需要转换的文件列表
    files_to_convert = [
        ('No_HK.json', 'No_HK.srs'),
        ('sing-box_ai.json', 'sing-box_ai.srs')
    ]
    
    # 执行转换
    for source_file, target_file in files_to_convert:
        json_path = os.path.join(rules_dir, source_file)
        srs_path = os.path.join(rules_dir, target_file)
        convert_json_to_srs(json_path, srs_path)

if __name__ == "__main__":
    main()
