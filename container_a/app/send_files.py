import io
import os
import re
import json
import time
import shutil
import logging
import socket
from datetime import datetime
from json2xml import json2xml
from json.decoder import JSONDecodeError
from cryptography.fernet import Fernet


class NotFileException(Exception):
    pass

class NotValidJSONException(Exception):
    pass

class XMLConversionException(Exception):
    pass

class ConnectionErrorException(Exception):
    pass

class SentErrorException(Exception):
    pass

class EncryptionException(Exception):
    pass

class PipelineSender:

    MOUNT_PATH = '/var/app/data/'
    SOURCE_PATH = MOUNT_PATH + 'to_send/'
    SENT_PATH = MOUNT_PATH + 'sent/'
    ERROR_PATH = MOUNT_PATH + 'sent_error/'

    HOST = os.getenv('SERVER_HOST')
    PORT = int(os.getenv('SERVER_PORT'))
    BUFFER_SIZE = int(os.getenv('BUFFER_SIZE'))
    SEPARATOR = os.getenv('SEPARATOR')

    PRIVATE_KEY = os.getenv('PRIVATE_KEY')

    def __init__(self, file_name):
        self.file_name = file_name
        self.path_file = self.SOURCE_PATH + self.file_name
        self.json = None
        self.xml = None
        self.xml_file_name = None
        self.logger = logging.getLogger('PipelineSender')

    def execute(self):
        self.log_info(f'Processing file.')
        try:
            self.valid_file()
            self.load_json()
            self.convert_to_xml()
            self.add_metadata()
            self.encrypt()
            self.send_xml()
            self.move_json()                
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.clean()
    
    def valid_file(self):
        if not os.path.isfile(self.path_file):
            msg = f'Path: "{self.path_file}" is not a file.'
            self.log_error(msg)
            raise NotFileException(msg)

    def load_json(self):
        with open(self.path_file, 'r') as f:
            try:
                self.json = json.load(f)
                self.log_info('Json file loaded.')
            except JSONDecodeError as e:
                self.log_error('Error decodng json.')
                raise NotValidJSONException(e)

    def convert_to_xml(self):
        try:
            self.xml = json2xml.Json2xml(
                self.json,
                wrapper="root",
                pretty=True
            ).to_xml().encode()
            self.log_info('File converted to xml succesfully.')
        except Exception as e:
            self.log_error('Error when converting json to xml.')
            raise XMLConversionException(e)

    def add_metadata(self):
        self.xml_file_name = self.rename_file(self.file_name)
        metadata = f"{self.xml_file_name}{self.SEPARATOR}".encode()
        self.xml_meta = metadata + self.xml
        self.log_info('Metadata added.')

    def encrypt(self):
        try:
            f = Fernet(self.PRIVATE_KEY)
            self.encrypted_xml = f.encrypt(self.xml_meta)
            self.log_info('File encrypted succesfully.')
        except Exception as e:
            self.log_error('Error while encrypting the file.')
            raise EncryptionException(e)

    def send_xml(self):
        s = self.connect_socket()
        try:
            f = io.BytesIO(self.encrypted_xml)
            self.log_info(f'Sending file: "{self.xml_file_name}"')
            while True:
                bytes_read = f.read(self.BUFFER_SIZE)
                if not bytes_read:
                    break
                s.sendall(bytes_read)
            self.log_info('File sent.')
        except Exception as e:
            self.log_error('Error while sending file.')
            raise SentErrorException(e)
        finally:
            s.close()

    def move_json(self):
        shutil.move(self.path_file, self.SENT_PATH + self.file_name)
        self.log_info(f'Json file moved to folder "{self.SENT_PATH}"')

    def clean(self):
        now = datetime.now().strftime("%Y%m%d_%H%M%S.%f")
        error_file_name = f'{self.file_name}_{now}'
        shutil.move(self.path_file, self.ERROR_PATH + error_file_name)
        self.log_info(f'File moved to folder "{self.ERROR_PATH}"".')

    def connect_socket(self):
        try:
            s = socket.socket()
            self.log_info(f'Connecting to {self.HOST}:{self.PORT}')
            s.connect((self.HOST, self.PORT))
            self.log_info('Connected.')
            return s
        except Exception as e:
            self.log_error(f'Error while establishing the connection.')
            raise ConnectionErrorException(e)

    def log_info(self, msg):
        self.logger.info(msg, extra={'file': f'{self.file_name} - '})

    def log_error(self, msg):
        self.logger.error(msg, extra={'file': f'{self.file_name} - '})

    @staticmethod
    def rename_file(file):
        return re.sub('.json$', '.xml', file)

    @classmethod
    def check_new_files(cls):
        return sorted([
            f for f in os.listdir(cls.SOURCE_PATH) if not f.startswith('.')
        ])

    @classmethod    
    def process_files(cls, files):
        for file in files:
            cls(file).execute()

if __name__=='__main__':
    from shared.logger import getLogger
    logger = getLogger('PipelineSender')
    logger.info("Waiting for json files...")
    while True:
        files = PipelineSender.check_new_files()
        if files:
            PipelineSender.process_files(files)
            logger.info("Waiting for json files...")
        time.sleep(1)
