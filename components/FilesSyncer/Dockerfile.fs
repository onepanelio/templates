FROM python:3.7
WORKDIR /home
RUN python3
COPY . /home
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/home/awscliv2.zip"
RUN unzip /home/awscliv2.zip
RUN /home/aws/install
# below env vars not required on onepanel
#ENV AWS_ACCESS_KEY_ID=""
#ENV AWS_SECRET_ACCESS_KEY=""
RUN python3 -m pip install --no-cache-dir -r /home/requirements.txt
