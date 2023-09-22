FROM python:3

RUN apt update && apt upgrade -y

WORKDIR /app

RUN apt install -y mc less netcat-openbsd emacs-nox python3 python3-pip xz-utils zip tar make htop

RUN pip3 install rich requests selenium tabulate reportlab

RUN mkdir /work

COPY src/startup.sh /startup.sh

COPY app/opendcx/. /app/opendcx

CMD [ "/bin/bash", "/startup.sh" ]
