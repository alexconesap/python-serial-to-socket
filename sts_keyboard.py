# TEST SCRIPT
# READ BARCODES (or whatever!) FROM KEYBOARD AND SEND THEM TO A COMPUTER SOCKET.
# IT USES KEYBOARD READING RATHER THAN SERIAL PORT. NO THREADS. NOT OPTIMIZED.
import socket
import configparser
import time
import sys
import os
import os.path
from datetime import datetime

_SCRIPT_PATH = os.path.dirname(__file__)
_CONFIG_FILE = os.path.join(_SCRIPT_PATH, 'sts.conf')

MAX_SOCKET_RETRIES = 2

host = ''
port = 0


def main():
    show_credits()
    read_config_or_die()

    while 1:
        barcode = input("Enter a barcode> ")
        if barcode in ["quit", "exit", "bye"]:
            break
        send_to_socket(barcode)

    print("")
    print("Finishing main thread. OK.")


def show_credits():
    print("")
    print("Network tools :: STS - Keyboard tester to Socket service, v1.0 Yakuma 2022")
    print("==========================================================================")
    print("This tool will work until it reads a barcode that contains the words 'exit', 'bye' or 'quit'")
    print("This is for testing purposes only. It reads data from keyboard.")
    print("")


def read_config_or_die():
    global host
    global port

    print("Using Python '{0}'".format(sys.executable))
    print("Process PID {0}".format(os.getpid()))

    if not os.path.isfile(_CONFIG_FILE):
        sys.stderr.write("Configuration file {0} not found\n".format(_CONFIG_FILE))
        sys.exit(-1)

    if not os.access(_CONFIG_FILE, os.R_OK):
        sys.stderr.write("Configuration file {0} not readable\n".format(_CONFIG_FILE))
        sys.exit(-2)

    config = configparser.ConfigParser()
    config.read(_CONFIG_FILE)

    host = config.get('hostinfo', 'write.ip')
    port = config.getint('hostinfo', 'write.port')

    print("")
    print("Configuration read:")
    print("  Network: host {0}:{1}".format(host, port))
    print("")


def log_error(message):
    print("ERROR " + message)


def send_to_socket(barcode):
    if barcode.strip() == "":
        return True

    connected = False
    retries = 0
    client_socket = None

    while not connected and retries < MAX_SOCKET_RETRIES:
        try:
            print("Sending barcode '{2}' to {0}:{1}".format(host, port, barcode))
            client_socket = socket.socket()
            client_socket.settimeout(2)
            client_socket.connect((host, port))
            connected = True
        except Exception as e:
            log_error("Connecting: {0}".format(e))
            retries += 1
            if client_socket is not None:
                client_socket.close()
            time.sleep(1)

    if connected:
        try:
            client_socket.send(barcode.encode())
            data = client_socket.recv(128).decode()

            if data == "ok":
                return True
            else:
                log_error("Wrong response received: '{0}'".format(data))
                return False
        except Exception as e:
            log_error("Sending barcode '{0}' got '{1}'".format(barcode, e))
            return False

    else:
        log_error(
            "Unable to connect to  {0}:{1}! Check remote host!".format(host, port))


if __name__ == '__main__':
    main()
