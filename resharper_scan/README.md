## 当前版本
resharper当前版本：2025.2.4

CodeCC可配置项仅包含[C#相关检查规则](https://www.jetbrains.com/help/resharper/Reference__Code_Inspections_CSHARP.html)

## 环境介绍
> 工具执行需要项目中包含`sln`文件

## 运行原理
1. 从 `resharper_scan/docker/Dockerfile`中构建包含最新版ReSharper CLI的容器
2.  运行前，工具自动根据 `resharper_scan/sdk/src/resharper_scan.py` 读取input.json 
3. 工具将匹配input.json对 `resharper_scan/sdk/resharper_inspections`所包含ReSharper默认检查规则的覆盖性修改 
4. 工具将生成.editorconfig文件，放入.sln文件同级目录下 
5. 在容器内执行 `jb inspectcode <your_solution_file>.sln -o=output.json`命令，ReSharper CLI自动读取EditorConfig
6. 检测结果将输出到output.json中，为[sarif](https://github.com/microsoft/sarif-tutorials)格式报告
