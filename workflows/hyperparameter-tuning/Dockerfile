FROM onepanel/vscode:0.17.0_code-server.3.8.0

LABEL maintainer="Onepanel, Inc. <support@onepanel.io>"

USER root

RUN apt-get update \
 && apt-get install -y jq \
 && rm -rf /var/lib/apt/lists/*

RUN pip --no-cache-dir install nni==2.0 ruamel_yaml==0.15.100 \
    'glances[web,gpu]' \
    albumentations \
    imgaug

COPY start.py /opt/onepanel/nni/

ENTRYPOINT ["python", "-u", "/opt/onepanel/nni/start.py"]
