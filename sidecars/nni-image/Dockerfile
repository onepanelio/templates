FROM pytorch/pytorch:latest
RUN apt-get update
RUN apt-get install zip unzip
RUN apt-get update
RUN apt-get install -y gcc g++ git curl wget nano
RUN python3 -m pip install urllib3==1.12 setuptools torch==1.4.0 torchvision==0.5.0 tensorboard onepanel-sdk==0.16.0b10
RUN python3 -m pip install --upgrade requests
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install -y nodejs
COPY nni-2.1-py3-none-manylinux1_x86_64.whl /workspace/
RUN python3 -m pip install nni-2.1-py3-none-manylinux1_x86_64.whl 
