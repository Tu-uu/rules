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
        
        srs_content = []
        for rule in data.get('rules', []):
            # 处理 domain
            for domain in rule.get('domain', []):
                srs_content.append(f"DOMAIN,{domain}")
            
            # 处理 domain_suffix
            for suffix in rule.get('domain_suffix', []):
                srs_content.append(f"DOMAIN-SUFFIX,{suffix}")
            
            # 处理 domain_keyword
            if 'domain_keyword' in rule:
                srs_content.append(f"DOMAIN-KEYWORD,{rule['domain_keyword']}")
        
        # 创建输出文件路径
        output_path = json_file_path.parent / f"{json_file_path.stem}.srs"
        
        # 写入SRS文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srs_content))
        
        logger.info(f"Successfully converted {json_file_path} to {output_path}")
        
    except Exception as e:
        logger.error(f"Error converting {json_file_path}: {str(e)}")

def process_rules_directory():
    rules_dir = Path('rules/rules')
    if not rules_dir.exists():
        logger.error("Rules directory not found")
        return
    
    for json_file in rules_dir.glob('*.json'):
        convert_json_to_srs(json_file)

if __name__ == '__main__':
    process_rules_directory()
