import getopt
import json
import os
import sys
import time
import xml
from xml.dom.minidom import Document
from os import walk
from sarif import loader
import resharper_scan

# 到22行都没啥用
enableChecker = []
checkerOptions = []
incrementalFiles = ""
# 保存扫描路径 工具路径忽略有问题，暂时不支持
scan_path = " "
scanType = "full"
# 忽略扫描路径
skipPath = []
projName = ""
windToolPath = "C:\\data\\codecc_software\\resharper_scan\\tool\\inspectcode.exe  "

class DefectObj(object):
    def __init__(self):
        self.filePath = ''
        self.line = 0
        self.checkerName = ''
        self.description = ''


class defect_pkg(object):
    def __init__(self):
        self.code = 0
        self.message = ''
        self.defects = list()

def loadInputJson(inputJson):
    # input.json 加载被放入resharper_scan.py中，此处无修改
    file = open(inputJson, encoding="UTF-8")
    jsonData = json.load(file)
    print(jsonData)
    checkCount = len(jsonData["openCheckers"])
    global projName
    projName = jsonData["projName"]

    global enableChecker
    global checkerOptions

    for i in range(0, checkCount):
        enableChecker.append(jsonData["openCheckers"][i]["checkerName"])

        if "checkerOptions" not in jsonData["openCheckers"][i]:
            continue

        checkerOptionsCount = len(jsonData["openCheckers"][i]["checkerOptions"])
        print("checkerOptionsCount: " + str(checkerOptionsCount))
        for check in range(0, checkerOptionsCount):
            checkName = jsonData["openCheckers"][i]["checkerName"]
            checkerOptionsName = jsonData["openCheckers"][i]["checkerOptions"][check]["checkerOptionName"]
            checkerOptionsValue = jsonData["openCheckers"][i]["checkerOptions"][check]["checkerOptionValue"]
            checkerOptions.append({"key": checkName + "." + checkerOptionsName,
                                   "value": checkerOptionsValue})

    if 'incrementalFiles' in jsonData:
        global incrementalFiles
        incrementalFilesCount = len(jsonData['incrementalFiles'])
        for i in range(incrementalFilesCount):
            if jsonData['incrementalFiles'][i].endswith('.py'):
                incrementalFiles += jsonData['incrementalFiles'][i] + " "

    if 'scanPath' in jsonData:
        global scan_path
        scan_path = jsonData['scanPath']

    if 'scanType' in jsonData:
        global scanType
        scanType = jsonData['scanType']

    if 'skipPaths' in jsonData:
        global skipPath
        skipPath = jsonData['skipPaths']

    print("enable checkers:" + str(enableChecker))
    print("checkerOptions:" + str(checkerOptions))

    file.close()

def write_output_json(filePath, defectData):
    print("start write output.json")
    open_file = open(str(filePath), "w")
    out_string = json.dumps(defectData, default=lambda obj: obj.__dict__)
    open_file.write(out_string)
    open_file.close()
    print("output.json write complete")

def execute_rsrp_cli_scan(output_file, input_json_file):
    """
    TODO: 执行ReSharper CLI扫描
    1. 容器内执行命令行 jb inspectcode <your_solution_file>.sln -o=output.json
    2. 运行前，需要将从input.json中提取并转换好的.editorconfig放入.sln文件同级目录下，ReSharper CLI会自动读取
    3. 运行后，需要删除.editorconfig临时文件

    未涵盖边界情况：
    1. 项目中如果已经有editorconfig文件，则需要额外处理
    """
    print("start execute resharper tool scan")
    start_time = time.perf_counter()  # 记录开始时间
    
    # 获取.sln文件路径
    try:
        sln_path = str(get_solution_file_path(scan_path))
    except Exception as e:
        error_defect = defect_pkg()
        error_defect.code = 500
        error_defect.message = str(e)
        write_output_json(output_file, error_defect)
        print("error: " + str(e))
        return
    
    # 确定.editorconfig文件的输出路径（放在.sln文件同级目录）
    sln_dir = os.path.dirname(sln_path)
    temp_editorconfig_path = os.path.join(sln_dir, ".editorconfig")

    # TODO: 生成.editorconfig文件;有可能与用户既有.editorconfig配置冲突，因此尝试捕错
    try:
        resharper_scan.main(input_json_file, temp_editorconfig_path)
    except Exception as e:
        error_defect = defect_pkg()
        error_defect.code = 500
        error_defect.message = f"生成.editorconfig文件失败: {str(e)}"
        write_output_json(output_file, error_defect)
        print("error: " + str(e))
        return
    
    # 执行扫描
    rsrp_cli_cmd = "jb inspectcode " + sln_path + " --jobs=4 -o=" + output_file
    os.system(rsrp_cli_cmd)
    elapsed_time = time.perf_counter() - start_time  # 计算耗时
    print("ReSharper CLI inspect code 结束, 耗时: {:.2f} 秒".format(elapsed_time))
    
    # 清理临时生成的editorconfig文件
    if os.path.exists(temp_editorconfig_path):
        os.remove(temp_editorconfig_path)
        print(f"已清理临时文件: {temp_editorconfig_path}")
    parse_rsrp_cli_output(output_file)


def parse_rsrp_cli_output(output_file):
    sarif_data = loader.load_sarif_file(output_file)
    # 删除输出的json报告
    if os.path.exists(output_file):
        os.remove(output_file)
    raise NotImplementedError("尚未实现利用sarif-tools解析ReSharper CLI输出的json报告；面对复杂分析结果，此依赖比直接json解析更快")



def get_solution_file_path(path):
    """
    TODO: 之前的实现有错误，此方法获取解决方案.sln路径, 需要基于Linux路径实现
    """
    filePath = ""
    outPath = [path + "\\.git", path + "\\.temp"]
    for root, dirs, files in os.walk(path):
        if str(root).startswith(outPath[1]) or str(root).startswith(outPath[0]):
            continue
        for file in files:
            if str(file).endswith(".sln"):
                filePath = root + "\\" + file
        if filePath != "":
            break
    if filePath == "":
        raise Exception("没有找到解决方案.sln路径！")
    return filePath


def main(argv):
    input_json_file = ""
    output_json_file = ""

    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["input=", "output="])
    except getopt.GetoptError:
        print('scan.py -i <inputfile> -o <outputfile> or --input <inputfile> -- output <output.json>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('scan.py -i <inputfile> -o <outputfile> or --input <inputfile> -- output <output.json>')
            sys.exit()
        elif opt in ("-i", "--input"):
            input_json_file = arg
        elif opt in ("-o", "--output"):
            output_json_file = arg
    if input_json_file == "" or output_json_file == "":
        print('scan.py -i <inputfile> -o <outputfile> or --input <inputfile> -- output <output.json>')
        sys.exit()
    loadInputJson(input_json_file)
    
    # 执行扫描（包括生成.editorconfig、执行扫描、清理临时文件）
    execute_rsrp_cli_scan(output_json_file, input_json_file)


if __name__ == "__main__":
    main(sys.argv[1:])
