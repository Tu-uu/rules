import requests
import yaml
import json
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 日志配置
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def create_session():
    """创建会话，增加网络请求的容错性"""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_rules(url, session):
    """从 URL 获取规则内容"""
    try:
        logging.info(f"Fetching URL: {url}")
        response = session.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
        if url.endswith('.json'):
            return json.loads(content)
        elif url.endswith(('.yaml', '.yml')):
            return yaml.safe_load(content)
        else:
            logging.error(f"Unsupported file type for URL: {url}")
            return None
    except Exception as e:
        logging.error(f"获取规则失败: {url}，错误: {e}")
        return None

def convert_rules(data):
    """转换规则格式为统一结构"""
    if not data:
        return None
    
    version = data.get("version", "1.0.0")
    result = {"version": version, "domain": [], "domain_suffix": [], "domain_keyword": []}

    try:
        if "rules" in data:
            for rule in data["rules"]:
                for key in result:
                    if isinstance(rule.get(key), list):
                        result[key].extend(rule.get(key))  # 处理 list 类型，使用 extend
                    elif rule.get(key):
                        result[key].append(rule.get(key))
        elif "payload" in data:
            for line in data["payload"]:
                if line.startswith("DOMAIN,"):
                    result["domain"].append(line.split(",", 1)[1])
                elif line.startswith("DOMAIN-SUFFIX,"):
                    result["domain_suffix"].append(line.split(",", 1)[1])
                elif line.startswith("DOMAIN-KEYWORD,"):
                    result["domain_keyword"].append(line.split(",", 1)[1])
        
        # 转换为唯一项，并且保持列表顺序
        return {k: sorted(list(set(v))) for k, v in result.items()}
    except Exception as e:
        logging.error(f"规则转换失败: {e}")
        return None

def process_group(group, output_dir, session):
    """处理规则组并生成文件"""
    logging.info(f"处理规则组: {group['name']}")
    rules_list = []

    # 并发获取规则内容
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_rules, url, session): url for url in group["urls"]}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            data = future.result()
            if data:
                converted = convert_rules(data)
                if converted:
                    rules_list.append(converted)

    # 合并规则
    merged_rules = {k: sorted({item for sublist in rules_list for item in sublist[k]}) for k in ["domain", "domain_suffix", "domain_keyword"]}

    # 确认合并后的规则非空
    if not merged_rules:
        logging.warning(f"规则组 {group['name']} 没有有效规则，跳过写入文件")
        return
    
    # 输出文件路径
    output_file = os.path.join(output_dir, f"{group['name']}.json")
    
    logging.info(f"准备写入文件 {output_file}，规则内容：{json.dumps(merged_rules, ensure_ascii=False, indent=2)}")
    
    # 写入输出文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"version": "1.0.0", "rules": [merged_rules]}, f, indent=2, ensure_ascii=False)
        logging.info(f"规则文件已生成: {output_file}")
    except Exception as e:
        logging.error(f"写入规则文件失败: {e}")

def main():
    # 配置文件路径
    config_path = os.path.join(os.path.dirname(__file__), "../config/config.json")
    output_dir = os.path.join(os.path.dirname(__file__), "../rules")
    os.makedirs(output_dir, exist_ok=True)

    # 加载配置
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 创建会话
    session = create_session()

    # 处理每个规则组
    for group in config["rule_groups"]:
        process_group(group, output_dir, session)

if __name__ == "__main__":
    main()
