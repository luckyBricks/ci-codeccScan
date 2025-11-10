# 此文件是参考文件，需要根据腾讯实际镜像做调整
# 拉取微软官方dotnet-sdk齐备的镜像，参考
# https://learn.microsoft.com/en-us/dotnet/architecture/microservices/net-core-net-framework-containers/official-net-docker-images
# 如果腾讯镜像中没有dotnet-sdk预装，则需要额外安装好dotnet-sdk，会慢
FROM mcr.microsoft.com/dotnet/sdk:8.0

# 安装Python
# RUN apt-get update && apt-get install -y python3 python3-pip && \
#     rm -rf /var/lib/apt/lists/*

# 全局安装sarif-tools，用于解析sarif格式的json报告
RUN pip3 install --system sarif-tools

RUN mkdir -p /usr/codecc/tool_scan
COPY sdk /usr/codecc/tool_scan/sdk

RUN dotnet new tool-manifest --name resharper
RUN dotnet tool install -g JetBrains.ReSharper.GlobalTools
ENV PATH="$PATH:/root/.dotnet/tools"
RUN dotnet tool restore
#RUN chmod -R 755 /usr/codecc/tool_scan

# 仅供测试阶段使用
COPY test /usr/codecc/tool_scan/test

WORKDIR /usr/codecc/tool_scan

CMD ["/bin/sh"]
