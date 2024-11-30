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
        
        # 使用集合来存储唯一的规则
        suffix_rules = set()
        domain_rules = set()
        keyword_rules = set()
        
        # 处理 rules 数组中的每个规则
        for rule in data.get('rules', []):
            # 处理 domain_suffix
            for suffix in rule.get('domain_suffix', []):
                suffix_rules.add(f"DOMAIN-SUFFIX,{suffix}")
            
            # 处理 domain
            for domain in rule.get('domain', []):
                domain_rules.add(f"DOMAIN,{domain}")
            
            # 处理 domain_keyword
            keywords = rule.get('domain_keyword', [])
            if isinstance(keywords, str):
                keywords = [keywords]
            elif isinstance(keywords, list):
                keywords = keywords
            else:
                keywords = []
            for keyword in keywords:
                keyword_rules.add(f"DOMAIN-KEYWORD,{keyword}")
        
        # 转换为列表并排序
        suffix_rules = sorted(suffix_rules)
        domain_rules = sorted(domain_rules)
        keyword_rules = sorted(keyword_rules)
        
        # 合并所有规则
        all_rules = suffix_rules + domain_rules + keyword_rules
        
        # 创建输出文件路径（在同一目录下）
        output_path = json_file_path.with_suffix('.srs')
        
        # 写入SRS文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_rules))
        
        logger.info(f"Successfully converted {json_file_path} to {output_path}")
        logger.info(f"Generated {len(all_rules)} rules")
        
    except Exception as e:
        logger.error(f"Error converting {json_file_path}: {str(e)}")
        raise e

def process_rules():
    rules_dir = Path('rules')
    logger.info(f"Looking for JSON files in: {rules_dir.absolute()}")
    
    if not rules_dir.exists():
        logger.error(f"Directory not found: {rules_dir}")
        return
    
    json_files = list(rules_dir.glob('*.json'))
    logger.info(f"Found JSON files: {[f.name for f in json_files]}")
    
    for json_file in json_files:
        logger.info(f"Processing {json_file}")
        convert_json_to_srs(json_file)

if __name__ == '__main__':
    process_rules()
