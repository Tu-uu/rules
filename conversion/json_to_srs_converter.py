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
        
        domains = set()
        domain_suffixes = set()
        domain_keywords = set()
        
        for rule in data.get('rules', []):
            domains.update(rule.get('domain', []))
            domain_suffixes.update(rule.get('domain_suffix', []))
            keywords = rule.get('domain_keyword', [])
            if isinstance(keywords, str):
                domain_keywords.add(keywords)
            elif isinstance(keywords, list):
                domain_keywords.update(keywords)
        
        # 去除被域名后缀覆盖的域名
        suffixes_list = sorted(domain_suffixes, key=lambda x: -len(x))
        for suffix in suffixes_list:
            domains = {domain for domain in domains if not domain.endswith(suffix)}
        
        # 去除域名关键词中包含在域名或域名后缀中的关键词
        domain_keywords = {kw for kw in domain_keywords if not any(kw in domain for domain in domains) and not any(kw in suffix for suffix in domain_suffixes)}
        
        srs_content = []
        for domain in domains:
            srs_content.append(f"DOMAIN,{domain}")
        for suffix in domain_suffixes:
            srs_content.append(f"DOMAIN-SUFFIX,{suffix}")
        for keyword in domain_keywords:
            srs_content.append(f"DOMAIN-KEYWORD,{keyword}")
        
        output_path = json_file_path.with_suffix('.srs')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srs_content))
        
        logger.info(f"成功将 {json_file_path} 转换为 {output_path}")
        logger.info(f"生成了 {len(srs_content)} 条规则")
        
    except Exception as e:
        logger.error(f"转换 {json_file_path} 时出错: {str(e)}")

def process_rules():
    rules_dir = Path('rules')
    for json_file in rules_dir.glob('*.json'):
        logger.info(f"处理 {json_file}")
        convert_json_to_srs(json_file)

if __name__ == '__main__':
    process_rules()
