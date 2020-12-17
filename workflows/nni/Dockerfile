FROM onepanel/jupyterlab:1.0.1

LABEL maintainer="Onepanel, Inc. <support@onepanel.io>"

USER root

RUN apt-get update \
 && apt-get install -y jq \
 && rm -rf /var/lib/apt/lists/*

RUN pip --no-cache-dir install nni==1.9 ruamel_yaml==0.11.14

COPY start.py /opt/nni/