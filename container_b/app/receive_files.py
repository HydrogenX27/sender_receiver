import os
import socket
import logging
from datetime import datetime
from cryptography.fernet import Fernet


class DecryptionException(Exception):
    pass

class MetadataException(Exception):
    pass

class PipelineToReceive:

    MOUNT_PATH = '/var/app/data/'
    RECEIVED_PATH = MOUNT_PATH + 'received/'
    ERROR_PATH = MOUNT_PATH + 'received_error/'

    SERVER_HOST = os.getenv('SERVER_HOST')
    SERVER_PORT = int(os.getenv('SERVER_PORT'))
    BUFFER_SIZE = int(os.getenv('BUFFER_SIZE'))
    SEPARATOR = os.getenv('SEPARATOR')

    PRIVATE_KEY = os.getenv('PRIVATE_KEY')

    def __init__(self, bytes_):
        self.encrypted_bytes = bytes_
        self.decrypted_string = None
        self.file_name = None
        self.xml = None
        self.logger = logging.getLogger('PipelineReceiver')

    def execute(self):
        self.log_info(f'Processing file.')
        try:
            self.decrypt()
            self.get_metadata()
            self.write_xml()
        except:
            self.log_error("Unexpected error.")
            self.clean()

    def decrypt(self):
        try:
            f = Fernet(self.PRIVATE_KEY)
            self.decrypted_string = f.decrypt(self.encrypted_bytes).decode()
            self.log_info('Decryption succesful.')
        except Exception as e:
            self.log_error('Error while decrypting data.')
            raise DecryptionException(e)

    def get_metadata(self):
        try:
            file_name, *remaining = self.decrypted_string.split(self.SEPARATOR)
            self.file_name = file_name
            self.xml = ''.join(remaining)
            self.log_info('Metadata obtained succesfully.')
        except Exception as e:
            self.log_error('Error while getting metadata.')
            raise MetadataException(e)

    def write_xml(self):
        with open(self.RECEIVED_PATH + self.file_name, 'w') as f:
            f.write(self.xml)
        self.log_info(f'File saved to {self.RECEIVED_PATH}.')

    def clean(self):
        now = datetime.now().strftime("%Y_%m_%d_%H:%M:%S.%f")
        error_file_name = f'{self.file_name}_{now}'
        with open(self.ERROR_PATH + error_file_name, 'wb') as f:
            f.write(self.encrypted_bytes)
        self.log_info(f'Encrypted stream saved to {self.ERROR_PATH}')

    def log_info(self, msg):
        self.logger.info(msg, extra={
            'file': f'{self.file_name} - ' if self.file_name else ''
        })

    def log_error(self, msg):
        self.logger.error(msg, extra={
            'file': f'{self.file_name} - '  if self.file_name else ''
        })

    @classmethod
    def wait_for_file(cls):
        try:
            client_socket, address = socket.accept() 
            logger.info(f"Connection established with {address}.")
            logger.info(f'Receiving file.')
            stream = b''
            while True:
                bytes_read = client_socket.recv(cls.BUFFER_SIZE)
                if not bytes_read:    
                    break
                stream += bytes_read
            return stream
        finally:
            client_socket.close()

    @classmethod
    def wait_for_files(cls, socket):
        try:
            socket.bind((cls.SERVER_HOST, cls.SERVER_PORT))
            socket.listen()
            logger = logging.getLogger('PipelineReceiver')
            logger.info(f'Listening on {cls.SERVER_HOST}:{cls.SERVER_PORT}')
            while True:
                logger.info('Waiting for xml files...')
                stream = cls.wait_for_file()
                cls(stream).execute()
        finally:
            socket.close()

if __name__=='__main__':
    from shared.logger import getLogger
    logger = getLogger('PipelineReceiver')
    socket = socket.socket()
    PipelineToReceive.wait_for_files(socket)