# 此文件是参考文件，需要根据腾讯实际镜像做调整
# 拉取微软官方dotnet-sdk齐备的镜像，参考
# https://learn.microsoft.com/en-us/dotnet/architecture/microservices/net-core-net-framework-containers/official-net-docker-images
# 如果腾讯镜像中没有dotnet-sdk预装，则需要额外安装好dotnet-sdk，会慢
FROM mcr.microsoft.com/dotnet/sdk:8.0

RUN mkdir -p /usr/codecc/tool_scan
COPY sdk /usr/codecc/tool_scan/sdk
COPY tool /usr/codecc/tool_scan/tool

RUN dotnet new tool-manifest --name resharper
RUN dotnet tool install -g JetBrains.ReSharper.GlobalTools
ENV PATH="$PATH:/root/.dotnet/tools"
RUN dotnet tool restore
#RUN chmod -R 755 /usr/codecc/tool_scan

# 仅供测试阶段使用
COPY test /usr/codecc/tool_scan/test

WORKDIR /usr/codecc/tool_scan

CMD ["/bin/sh"]
