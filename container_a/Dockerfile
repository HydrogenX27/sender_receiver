from python:3.10.0-bullseye

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

CMD [ "python", "./send_files.py" ]