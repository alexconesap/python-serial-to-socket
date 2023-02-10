# TEST SCRIPT. SOCKET SERVER
import socket
import configparser
import sys
import os
import os.path

_SCRIPT_PATH = os.path.dirname(__file__)
_CONFIG_FILE = os.path.join(_SCRIPT_PATH, 'sts.conf')

host = '127.0.0.1'
port = 15010
end_char = 0


def main():
    show_credits()
    read_config_or_die()

    print("")
    print("Waiting for requests")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)

    while 1:
        conn, addr = s.accept()
        data = conn.recv(128)
        if data:
            print("Received {0} from {1}".format(data, addr))
            conn.sendall("ok".encode())


def show_credits():
    print("")
    print("Network tools :: STS - Sample server for testing, v1.2 Yakuma 2022")
    print("===================================================================")
    print("")


def read_config_or_die():
    global host
    global port
    global end_char

    print("Using Python '{0}'".format(sys.executable))
    print("Process PID {0}".format(os.getpid()))

    defaults = False

    if not os.path.isfile(_CONFIG_FILE):
        sys.stderr.write("Configuration file {0} not found. Using defaults.\n".format(_CONFIG_FILE))
        defaults = True

    if not os.access(_CONFIG_FILE, os.R_OK):
        sys.stderr.write("Configuration file {0} not readable. Using defaults.\n".format(_CONFIG_FILE))
        defaults = True

    if not defaults:
        config = configparser.ConfigParser()
        config.read(_CONFIG_FILE)

        port = config.getint('hostinfo', 'write.port')
        end_char = config.getint('hostinfo', 'read.end_char')

        print("")
        print("Configuration used:")
    else:
        print("Defaults:")

    print("  Network: host {0}:{1}".format(host, port))


def log_error(text):
    sys.stderr.write("ERROR " + text + "\n")


if __name__ == '__main__':
    main()
