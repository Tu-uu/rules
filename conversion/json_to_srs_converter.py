import json
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_json_to_srs(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 创建三个列表分别存储不同类型的规则
        suffix_rules = []
        domain_rules = []
        keyword_rules = []
        
        # 处理 rules 数组中的每个规则
        for rule in data.get('rules', []):
            # 处理 domain_suffix
            for suffix in rule.get('domain_suffix', []):
                suffix_rules.append(f"DOMAIN-SUFFIX,{suffix}")
            
            # 处理 domain
            for domain in rule.get('domain', []):
                domain_rules.append(f"DOMAIN,{domain}")
            
            # 处理 domain_keyword
            if 'domain_keyword' in rule:
                keyword = rule['domain_keyword']
                if isinstance(keyword, str):
                    keyword_rules.append(f"DOMAIN-KEYWORD,{keyword}")
                elif isinstance(keyword, list):
                    for kw in keyword:
                        keyword_rules.append(f"DOMAIN-KEYWORD,{kw}")
        
        # 对每种类型的规则进行排序
        suffix_rules.sort()
        domain_rules.sort()
        keyword_rules.sort()
        
        # 按顺序合并所有规则
        all_rules = suffix_rules + domain_rules + keyword_rules
        
        # 创建输出文件路径
        output_path = json_file_path.with_suffix('.srs')
        
        # 写入SRS文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_rules))
        
        logger.info(f"Successfully converted {json_file_path} to {output_path}")
        logger.info(f"Generated {len(all_rules)} rules")
        
    except Exception as e:
        logger.error(f"Error converting {json_file_path}: {str(e)}")

def process_rules():
    # 处理 rules 目录下的 JSON 文件
    rules_dir = Path('rules')
    
    # 处理 rules 目录下的所有 JSON 文件
    for json_file in rules_dir.glob('*.json'):
        logger.info(f"Processing {json_file}")
        convert_json_to_srs(json_file)

if __name__ == '__main__':
    process_rules()
