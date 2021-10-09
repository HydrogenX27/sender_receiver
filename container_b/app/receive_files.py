import socket
import logging


class PipelineToReceive:

    MOUNT_PATH = '/var/app/data/'
    DEST_PATH = MOUNT_PATH + 'received/'

    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 5000
    BUFFER_SIZE = 4096
    SEPARATOR = "||"

    def __init__(self):
        self.logger = logging.getLogger('PipelineToSend')

    @classmethod
    def wait_for_files(cls, socket):
        try:
            socket.bind((cls.SERVER_HOST, cls.SERVER_PORT))
            socket.listen()
            logger = logging.getLogger('PipelineToSend')
            logger.info(f'Listening on {cls.SERVER_HOST}:{cls.SERVER_PORT}')
            while True:
                try:
                    logger.info('Waiting for xml files...')
                    client_socket, address = socket.accept() 
                    logger.info(f"Connection established with {address}.")
                    received = client_socket.recv(cls.BUFFER_SIZE).decode()
                    filename, *remaining = received.split(cls.SEPARATOR)
                    logger.info('Receiving file ' + filename)
                    with open(cls.DEST_PATH + filename, "wb") as f:
                        f.write(''.join(remaining).encode())
                        while True:
                            bytes_read = client_socket.recv(cls.BUFFER_SIZE)
                            if not bytes_read:    
                                break
                            f.write(bytes_read)
                finally:
                    client_socket.close()
        finally:
            socket.close()

if __name__=='__main__':
    from shared.logger import getLogger
    logger = getLogger('PipelineToSend')
    socket = socket.socket()
    PipelineToReceive.wait_for_files(socket)