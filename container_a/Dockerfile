FROM python:3.10.0-bullseye

ARG USER=app

RUN apt update && apt upgrade -y && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1000 $USER; \
    adduser --system --ingroup $USER --uid 1000 --shell /bin/bash $USER; \
    echo $USER:$USER | chpasswd;

WORKDIR /home/$USER

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

RUN chown -R $USER:$USER /home/$USER;

USER $USER

CMD [ "python", "./send_files.py" ]