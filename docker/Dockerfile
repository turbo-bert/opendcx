FROM python:3

RUN apt update && apt upgrade -y

WORKDIR /app

RUN apt install -y mc less netcat-openbsd emacs-nox python3 python3-pip xz-utils zip tar make htop curl

RUN pip3 install rich requests selenium tabulate reportlab

RUN mkdir -p /app/tw && curl -L -o /app/tw/__init__.py https://raw.githubusercontent.com/turbo-bert/py-tw/main/tw/__init__.py

RUN mkdir /work

COPY src/startup.sh /startup.sh

COPY app/opendcx/. /app/opendcx

CMD [ "/bin/bash", "/startup.sh" ]
