import os
import io
import socket
import logging


class PipelineToReceive:

    MOUNT_PATH = '/var/app/data/'
    RECEIVED_PATH = MOUNT_PATH + 'received/'
    ERROR_PATH = MOUNT_PATH + 'received_error/'

    SERVER_HOST = os.getenv('SERVER_HOST')
    SERVER_PORT = int(os.getenv('SERVER_PORT'))
    SEPARATOR = os.getenv('SEPARATOR')
    BUFFER_SIZE = int(os.getenv('BUFFER_SIZE'))

    def __init__(self, file_name, stream):
        self.file_name = file_name
        self.stream = stream
        self.logger = logging.getLogger('PipelineReceiver')
        self.log_details = {
            'extra' : {
                'file': self.file_name + ' - '
            }
        }

    def execute(self):
        self.logger.info(f'Processing file.', **self.log_details)
        try:
            self.write_xml()
        except:
            self.logger.exception("Unexpected error.", **self.log_details)
            self.clean()

    def write_xml(self):
        with open(self.RECEIVED_PATH + self.file_name, 'wb') as f:
            f.write(self.stream.getbuffer())

    def clean(self):
        with open(self.ERROR_PATH + self.file_name, 'wb') as f:
            f.write(self.stream.getbuffer())

    @classmethod
    def wait_for_file(cls):
        try:
            client_socket, address = socket.accept() 
            logger.info(f"Connection established with {address}.")
            received = client_socket.recv(cls.BUFFER_SIZE).decode()
            file_name, *remaining = received.split(cls.SEPARATOR)
            logger.info(f'Receiving file {file_name}')
            stream = io.BytesIO()
            stream.write(''.join(remaining).encode())
            while True:
                bytes_read = client_socket.recv(cls.BUFFER_SIZE)
                if not bytes_read:    
                    break
            return file_name, stream
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
                file_name, stream = cls.wait_for_file()
                cls(file_name, stream).execute()
        finally:
            socket.close()

if __name__=='__main__':
    from shared.logger import getLogger
    logger = getLogger('PipelineReceiver')
    socket = socket.socket()
    PipelineToReceive.wait_for_files(socket)