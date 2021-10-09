import io
import os
import re
import json
import time
import shutil
import logging
import socket
from dicttoxml import dicttoxml
from json.decoder import JSONDecodeError


class NotFileException(Exception):
    pass

class NotValidJSONException(Exception):
    pass

class PipelineToSend:

    MOUNT_PATH = '/var/app/data/'
    SOURCE_PATH = MOUNT_PATH + 'to_send/'
    SENT_PATH = MOUNT_PATH + 'sent/'
    ERROR_PATH = MOUNT_PATH + 'sent_error/'

    HOST = "host.docker.internal"
    PORT = 5000
    SEPARATOR = "||"
    BUFFER_SIZE = 4096

    def __init__(self, file):
        self.file = file
        self.path_file = self.SOURCE_PATH + file
        self.json = None
        self.xml = None
        self.xml_file_name = None
        self.logger = logging.getLogger('PipelineToSend')
        self.log_details = {
            'extra' : {
                'file': self.file + ' - '
            }
        }

    def execute(self):
        self.logger.info(f'Processing file', **self.log_details)
        try:
            self.valid_file()
            self.load_json()
            self.convert_to_xml()
            self.cipher()
            self.send_xml()
            self.move_json()                
        except:
            self.logger.exception("Unexpected error.", **self.log_details)
            self.clean()
    
    def valid_file(self):
        if not os.path.isfile(self.path_file):
            msg = f'Path: "{self.path_file}" is not a file.'
            self.logger.error(msg, **self.log_details)
            raise NotFileException(msg)

    def load_json(self):
        with open(self.path_file, 'r') as f:
            try:
                self.json = json.load(f)
                self.logger.info('Json file loaded.', **self.log_details)
            except JSONDecodeError as e:
                self.logger.error('Error decodng json.', **self.log_details)
                raise NotValidJSONException(e.msg)

    def convert_to_xml(self):
        try:
            self.xml = dicttoxml(self.json)
            self.logger.info('File converted to xml succesfully.', **self.log_details)
        except:
            self.logger.error('Error when converting json to xml.', **self.log_details)
            raise Exception

    def cipher(self):
        pass

    def clean(self):
        shutil.move(self.path_file, self.ERROR_PATH + self.file)
        self.logger.error(f'File moved to {self.ERROR_PATH}.', **self.log_details)

    def send_xml(self):
        self.xml_file_name = self.rename_file(self.file)
        s = socket.socket()
        self.logger.info(f'Connecting to {self.HOST}:{self.PORT}', **self.log_details)
        s.connect((self.HOST, self.PORT))
        self.logger.info('Connected.', **self.log_details)
        self.logger.info(
            f'Sending file {self.xml_file_name}',
            **self.log_details
        )
        f = io.BytesIO(f"{self.xml_file_name}{self.SEPARATOR}".encode() + self.xml)
        while True:
            bytes_read = f.read(self.BUFFER_SIZE)
            if not bytes_read:
                break
            s.sendall(bytes_read)
        self.logger.info('File sent.', **self.log_details)
        s.close()

    def move_json(self):
        shutil.move(self.path_file, self.SENT_PATH + self.file)
        self.logger.info(f'Json file moved to folder "{self.SENT_PATH}"', **self.log_details)

    @classmethod
    def check_new_files(cls):
        return os.listdir(cls.SOURCE_PATH)

    @classmethod    
    def process_files(cls, files):
        for file in files:
            cls(file).execute()
            time.sleep(5)

    @staticmethod
    def rename_file(file):
        return re.sub('.json$', '.xml', file)


if __name__=='__main__':
    from shared.logger import getLogger
    logger = getLogger('PipelineToSend')
    logger.info("Waiting for json files...")
    while True:
        files = PipelineToSend.check_new_files()
        if files:
            PipelineToSend.process_files(files)
            logger.info("Waiting for json files...")
        time.sleep(1)
