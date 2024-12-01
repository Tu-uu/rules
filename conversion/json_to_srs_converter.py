import os
import logging
import json
import yaml
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_session(user_agent):
    """创建会话，增加网络请求的容错性"""
    session = requests.Session()
    session.headers.update({'User-Agent': user_agent})
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

        # 根据文件类型解析内容
        if url.endswith('.json'):
            return json.loads(content)
        elif url.endswith(('.yaml', '.yml')):
            return yaml.safe_load(content)
        elif url.endswith(('.txt', '.conf')):
            # 解析简单文本规则，按行分割
            lines = content.splitlines()
            payload = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
            return {"payload": payload}
        else:
            logging.error(f"Unsupported file type for URL: {url}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"网络请求失败: {url}, 错误: {e}")
        return None
    except Exception as e:
        logging.error(f"获取规则失败: {url}, 错误: {e}")
        return None

def convert_rules(fetched_data):
    """转换规则格式为统一结构，并优化规则"""
    if not fetched_data:
        return None

    converted_rules = {"domain": [], "domain_suffix": [], "domain_keyword": []}

    try:
        if "rules" in fetched_data:
            # 支持 JSON/YAML 格式的规则
            for rule in fetched_data["rules"]:
                for key in converted_rules:
                    if isinstance(rule.get(key), list):
                        converted_rules[key].extend(rule.get(key, []))
                    elif rule.get(key):
                        converted_rules[key].append(rule.get(key))
        elif "payload" in fetched_data:
            # 支持 TXT/CONF 的规则
            for line in fetched_data["payload"]:
                if line.startswith("DOMAIN,"):
                    converted_rules["domain"].append(line.split(",", 1)[1])
                elif line.startswith("DOMAIN-SUFFIX,"):
                    converted_rules["domain_suffix"].append(line.split(",", 1)[1])
                elif line.startswith("DOMAIN-KEYWORD,"):
                    converted_rules["domain_keyword"].append(line.split(",", 1)[1])

        # 优化规则：去重并移除冗余
        converted_rules["domain"] = sorted(set(converted_rules["domain"]))
        converted_rules["domain_suffix"] = sorted(set(converted_rules["domain_suffix"]) - set(converted_rules["domain"]))
        converted_rules["domain_keyword"] = sorted(set(converted_rules["domain_keyword"]))

        # 去除 domain_keyword 中可能包含的 domain 或 domain_suffix
        converted_rules["domain_keyword"] = [
            kw for kw in converted_rules["domain_keyword"]
            if not any(kw in item for item in converted_rules["domain"] + converted_rules["domain_suffix"])
        ]

        return converted_rules
    except Exception as e:
        logging.error(f"规则转换失败: {e}")
        return None

def process_group(group, output_dir, session):
    """处理规则组并生成 JSON 文件"""
    logging.info(f"处理规则组: {group['name']}")
    converted_rules_list = []

    # 并发获取规则内容
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_url = {executor.submit(fetch_rules, url, session): url for url in group["urls"]}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            fetched_data = future.result()
            if fetched_data:
                converted_rules = convert_rules(fetched_data)
                if converted_rules:
                    converted_rules_list.append(converted_rules)

    # 合并规则
    merged_domain = set()
    merged_domain_suffix = set()
    merged_domain_keyword = set()

    for rules in converted_rules_list:
        merged_domain.update(rules["domain"])
        merged_domain_suffix.update(rules["domain_suffix"])
        merged_domain_keyword.update(rules["domain_keyword"])

    merged_domain_suffix = merged_domain_suffix - merged_domain
    merged_domain_keyword = merged_domain_keyword - merged_domain - merged_domain_suffix

    merged_rules = {
        "version": "1.0.0",
        "rules": [
            {
                "domain": sorted(merged_domain),
                "domain_suffix": sorted(merged_domain_suffix),
                "domain_keyword": sorted(merged_domain_keyword)
            }
        ]
    }

    # 确认合并后的规则非空
    if not any(merged_rules["rules"][0].values()):
        logging.warning(f"规则组 {group['name']} 没有有效规则，跳过写入文件")
        return

    # 输出文件路径
    output_file = os.path.join(output_dir, f"{group['name']}.json")

    logging.info(f"准备写入文件 {output_file}，规则内容：{json.dumps(merged_rules, ensure_ascii=False, indent=2)}")

    # 写入 JSON 文件
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged_rules, f, indent=2, ensure_ascii=False)
        logging.info(f"规则文件已生成: {output_file}")
    except Exception as e:
        logging.error(f"写入规则文件失败: {e}")

def main(config_path, output_dir, user_agent):
    os.makedirs(output_dir, exist_ok=True)

    # 加载配置
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 创建会话
    session = create_session(user_agent)

    # 处理每个规则组
    for group in config["rule_groups"]:
        process_group(group, output_dir, session)

if __name__ == "__main__":
    # 配置参数
    config_path = os.path.join(os.path.dirname(__file__), "../config/config.json")
    output_dir = os.path.join(os.path.dirname(__file__), "../rules")
    user_agent = "GitHub Action/1.0"

    main(config_path, output_dir, user_agent)
