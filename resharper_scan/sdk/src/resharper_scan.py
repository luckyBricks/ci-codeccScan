import json
import os
from os import walk


# resharper_scan/sdk/resharper_inspections目录中存放的是所有将添加到bkci检查中的规则

def get_all_bkci_supported_inspections():
    """
    读取所有支持的检测规则，即resharper_scan/sdk/resharper_inspections中的inspections文件
    返回inspections对象
    """
    # 使用相对路径定位inspections目录
    inspections_dir = os.path.join(os.path.dirname(__file__), "..", "resharper_inspections")
    bkci_supported_inspections = []

    # 遍历目录查找inspection配置文件
    for (dirpath, dirnames, filenames) in walk(inspections_dir):
        for filename in filenames:
            if 'inspections' in filename and filename.endswith(".json"):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, encoding="UTF-8") as file:
                        json_data = json.load(file)
                        if 'inspections' in json_data:
                            bkci_supported_inspections.extend(json_data['inspections'])
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Failed to read {filepath}: {e}")
        break  # 只遍历顶层目录

    return bkci_supported_inspections

def update_severity_by_inspection_id(input_checkers, inspections):
    """
    从input.json中的openCheckers获取修改的severity信息，替换掉默认severity
    """
    id_checker_map = {item['checkerName']: item['severity'] for item in input_checkers}
    for inspection in inspections:
        if inspection['id'] in id_checker_map:
            inspection['defaultSeverity'] = id_checker_map[inspection['id']]

def replace_severity_from_input(input_json_path):
    """
    替换inspections对象中的severity为指定的severity
    """
    try:
        with open(input_json_path, encoding="UTF-8") as input_json_file:
            input_json = json.load(input_json_file)
    except (json.JSONDecodeError, IOError) as e:
        raise ValueError(f"Failed to read input JSON file {input_json_path}: {e}")

    inspections = get_all_bkci_supported_inspections()
    update_severity_by_inspection_id(input_json.get('openCheckers', []), inspections)

    return inspections

def generate_editorconfig_from_inspections(inspections):
    """
    从inspections对象中提取editorConfig和defaultSeverity字段
    生成editorconfig文件格式的配置行
    返回配置行列表
    """
    config_lines = []
    severity_map = {
        'Error': 'error',
        'Warning': 'warning',
        'Suggestion': 'suggestion',
        'Hint': 'hint'
    }

    for inspection in inspections:
        editor_config = inspection.get('editorConfig')
        default_severity = inspection.get('defaultSeverity')

        if editor_config and default_severity:
            # 将ReSharper的severity映射为editorconfig的severity
            severity_lower = severity_map.get(default_severity, default_severity.lower())
            config_line = f"{editor_config} = {severity_lower}"
            config_lines.append(config_line)

    return config_lines

def update_editorconfig_template(template_path, config_lines, output_path=None):
    """
    读取editorconfig_template文件，将生成的配置行添加入其中
    如果output_path为None，则覆盖原文件；生产环境中不要使用
    """
    if output_path is None:
        output_path = template_path

    # 读取模板文件
    with open(template_path, 'r', encoding='UTF-8') as f:
        template_content = f.read()

    # 添加配置行
    config_content = '\n'.join(config_lines)
    final_content = template_content.rstrip() + '\n\n' + config_content + '\n'

    # 写入文件
    with open(output_path, 'w', encoding='UTF-8') as f:
        f.write(final_content)

    return output_path


# 测试用
if __name__ == "__main__":
    input_json_path = os.path.join(os.path.dirname(__file__), "..", "..", "test", "input.json")
    template_path = os.path.join(os.path.dirname(__file__), "..", "resharper_configs", "editorconfig.template")
    temp_editorconfig_path = os.path.join(os.path.dirname(__file__), "..", "..", "test", "SampleConsoleApp", ".editorconfig")

    # 1. 获取并替换severity的inspections
    inspections = replace_severity_from_input(input_json_path)

    # 2. 从inspections生成editorconfig配置行
    config_lines = generate_editorconfig_from_inspections(inspections)

    # 3. 更新editorconfig_template文件
    output_path = update_editorconfig_template(template_path, config_lines, temp_editorconfig_path)

    print(f"已生成 {len(config_lines)} 条配置规则")
    print(f"editorconfig文件已更新: {output_path}")
