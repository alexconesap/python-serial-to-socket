# TEST SCRIPT
# READ BARCODES (or whatever!) FROM KEYBOARD AND SEND THEM TO A COMPUTER SOCKET.
# IT USES KEYBOARD READING RATHER THAN SERIAL PORT. IT USES THREADS. NOT OPTIMIZED.
import socket
from threading import Thread, Lock
import configparser
import time
import sys
import os
import os.path
from datetime import datetime

_SCRIPT_PATH = os.path.dirname(__file__)
_CONFIG_FILE = os.path.join(_SCRIPT_PATH, 'sts.conf')
_LOG_FILE = os.path.join(_SCRIPT_PATH, 'storage/sts.log')
_DUMP_FILE = os.path.join(_SCRIPT_PATH, 'storage/dump.data')

_BUZZER_PIN = 23
_MAX_SERIAL_RETRIES = 5
_MAX_SOCKET_RETRIES = 5
_AUTO_REBOOT = False

mutex = Lock()
barcode_data = []
host = ''
port = 0


def main():
    show_credits()
    read_config_or_die()

    th_keyboard = Thread(target=read_from_keyboard_thread, args=())
    th_keyboard.start()


def show_credits():
    print("")
    print("Network tools :: STS - Serial to Socket tester, v1.3 Yakuma 2022")
    print("================================================================")
    print("Type 'exit', 'bye' or 'quit' to finish the execution.")
    print("")


def read_config_or_die():
    global host
    global port

    print("Using Python '{0}'".format(sys.executable))
    print("Process PID {0}".format(os.getpid()))

    if not os.path.isfile(_CONFIG_FILE):
        sys.stderr.write(
            "Configuration file {0} not found\n".format(_CONFIG_FILE))
        sys.exit(-1)

    if not os.access(_CONFIG_FILE, os.R_OK):
        sys.stderr.write(
            "Configuration file {0} not readable\n".format(_CONFIG_FILE))
        sys.exit(-2)

    config = configparser.ConfigParser()
    config.read(_CONFIG_FILE)

    host = config.get('hostinfo', 'write.ip')
    port = config.getint('hostinfo', 'write.port')

    print("")
    print("Configuration read:")
    print("  Network: host {0}:{1}".format(host, port))


def beep(duration_seconds=0.5):
    try:
        time.sleep(duration_seconds)
    except Exception as e:
        log_error("Error on beep {0}".format(e))


def beep_ack_communications_ok():
    beep(0.15)
    beep(0.15)


def beep_ack_communications_wrong():
    beep(0.25)
    beep(0.25)
    beep(0.25)


def read_from_keyboard_thread():
    print("")
    print("Reading data from keyboard. Type exit, quit or bye to exit.")
    print(
        "Note that when data is being sent to the remote host the focus on"
        "the console will be lost but you can still type more barcodes."
        "Not necessary to wait for responses.")

    print("")

    finish_socket_thread = False
    id = 0

    th_socket = Thread(target=socket_thread, args=(
        id, lambda: finish_socket_thread))
    th_socket.start()

    while 1:
        barcode = input("Enter a barcode> ")
        if barcode == "quit" or barcode == "exit" or barcode == "bye":
            break
        add_barcode(barcode)

    finish_socket_thread = True

    print("")
    print("Finishing main thread. OK.")


def add_barcode(barcode):
    b_to_append = barcode.strip().replace("\n", "").replace("\r", "").replace("\t", "")
    b_to_append = ''.join(e for e in b_to_append if e.isalnum())

    if b_to_append == "":
        return

    mutex.acquire()
    try:
        print("Barcode queued '{0}'".format(b_to_append))

        barcode_data.append(b_to_append)

        beep()
    finally:
        mutex.release()


def log_error(text):
    sys.stderr.write("ERROR " + text + "\n")
    with open(_LOG_FILE, "a") as f:
        # [2020-01-02 07:44:28] ERROR
        f.write(datetime.now().strftime(
            "[%Y-%m-%d %H:%M:%S]") + " ERROR " + text + "\n")


def socket_thread(id, stop):
    while 1:
        if stop():
            print("Finishing socket thread. OK.")
            break

        time.sleep(.250)
        mutex.acquire()

        while len(barcode_data) != 0:
            barcode = barcode_data[0]
            if send_to_socket(barcode):
                del barcode_data[0]

        mutex.release()


def send_to_socket(barcode):
    if barcode.strip() == "":
        return True

    connected = False
    retries = 0
    client_socket = None

    while not connected and retries < _MAX_SOCKET_RETRIES:
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
                beep_ack_communications_wrong()
                return False

        except Exception as e:
            log_error("Sending barcode '{0}' got '{1}'".format(barcode, e))
            beep_ack_communications_wrong()
            return False

    else:
        log_error(
            "Unable to connect to  {0}:{1}! Check remote host!".format(host, port))
        beep_ack_communications_wrong()


if __name__ == '__main__':
    main()
