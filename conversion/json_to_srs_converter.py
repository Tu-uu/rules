import json
import os
from pathlib import Path
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_json_to_srs(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        srs_content = []
        for rule_type in ['domain', 'domain_suffix', 'domain_keyword']:
            if rule_type in data:
                for item in data[rule_type]:
                    if rule_type == 'domain':
                        srs_content.append(f"DOMAIN,{item}")
                    elif rule_type == 'domain_suffix':
                        srs_content.append(f"DOMAIN-SUFFIX,{item}")
                    elif rule_type == 'domain_keyword':
                        srs_content.append(f"DOMAIN-KEYWORD,{item}")
        
        # 创建输出文件路径
        output_path = Path('rules/rules') / f"{json_file_path.stem}.srs"
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入SRS文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srs_content))
        
        logger.info(f"Successfully converted {json_file_path} to {output_path}")
        
    except Exception as e:
        logger.error(f"Error converting {json_file_path}: {str(e)}")

def process_rules():
    # 源文件目录
    rules_dir = Path('rules')
    target_dir = Path('rules/rules')
    
    # 确保目标目录存在
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 处理根目录下的 JSON 文件
    for json_file in rules_dir.glob('*.json'):
        if json_file.name != 'openai.json':  # 排除 openai.json
            convert_json_to_srs(json_file)

if __name__ == '__main__':
    process_rules()
