FROM python:3.10-slim-bookworm AS light-builder
RUN apt-get update && apt-get install -y --no-install-recommends g++ && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY native/nodka_light_bridge.cpp ./
COPY SDK/NKIOSDK_Linux_V5.0.4/LinuxSDK/Lib/include/NKLCLIB.h ./
COPY SDK/NKIOSDK_Linux_V5.0.4/LinuxSDK/Lib/GCC_11.04/libNKLCLIB.so ./
RUN test "$(uname -m)" = x86_64 && mkdir /out && cp libNKLCLIB.so /out/ && g++ -std=c++11 -O2 -fPIC -shared -pthread nodka_light_bridge.cpp -I. -L/out -lNKLCLIB -Wl,-rpath,'$ORIGIN' -Wl,-z,defs -o /out/libagv_nodka_light.so

FROM python:3.10-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libusb-1.0-0 libstdc++6 libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.docker.txt ./
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --index-url "$PIP_INDEX_URL" -r requirements.docker.txt
COPY --from=light-builder /out/ /app/third_party/nodka/lib/
COPY deploy/nkio_config.ini /app/third_party/nodka/config/nkio_config.ini
COPY deploy/check_runtime.py /app/deploy/check_runtime.py
COPY SDK/MvImport/ /app/SDK/MvImport/
COPY agv_vision/ /app/agv_vision/
EXPOSE 8088
CMD ["python", "-m", "agv_vision.main", "--config", "agv_vision/config/settings_online.yaml", "serve"]
