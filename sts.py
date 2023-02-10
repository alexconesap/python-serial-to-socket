import socket
from threading import Thread, Lock
import configparser
import serial
import time
import sys
import os
import os.path
import RPi.GPIO as GPIO
from datetime import datetime

# import serial_reader as sreader

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
serial_port = ''
end_char = 0


def main():
    show_credits()
    read_config_or_die()

    th_serial = Thread(target=read_from_serialport_thread, args=())
    th_serial.start()


def show_credits():
    print("")
    print("Network tools :: STS - Serial to Socket service, v1.78 Yakuma 2022")
    print("==================================================================")
    print("This tool will work until it reads a barcode that contains the words 'exit', 'bye' or 'quit'")
    print("")


def read_config_or_die():
    global host
    global port
    global serial_port
    global end_char

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
    serial_port = config.get('hostinfo', 'read.port')
    end_char = config.getint('hostinfo', 'read.end_char')

    print("")
    print("Configuration read:")
    print("  Serial port: {0}".format(serial_port))
    print("  Network: host {0}:{1}".format(host, port))

    # Configure GPIO (required by the buzzer - beeping)
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(_BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)

    read_dump_file()


def dump_list():
    if len(barcode_data) > 0:
        print("Dump of buffered data:")
        for b in barcode_data:
            dump_bc_to_file("{0}".format(b))


def dump_bc_to_file(bc):
    print("  Barcode: {0}".format(bc))
    with open(_DUMP_FILE, "a") as f:
        f.write(bc + "\n")


def beep(duration_seconds=0.5):
    try:
        GPIO.output(_BUZZER_PIN, GPIO.HIGH)
        time.sleep(duration_seconds)
        GPIO.output(_BUZZER_PIN, GPIO.LOW)
    except Exception as e:
        log_error("Error on beep {0}".format(e))


def beep_ack_communications_ok():
    beep(0.15)
    beep(0.15)


def beep_ack_communications_wrong():
    beep(0.25)
    beep(0.25)
    beep(0.25)


def read_dump_file():
    if not os.path.isfile(_DUMP_FILE):
        return

    try:
        with open(_DUMP_FILE, "r") as f:
            lines = f.readlines()
            for bc in lines:
                add_barcode(bc)
    finally:
        os.remove(_DUMP_FILE)


def reboot_device():
    return
    # print ("Rebooting device")
    # os.system("sudo shutdown -r")


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


def read_from_serialport_thread():
    ser = open_serial_port()

    if not ser:
        log_error("Opening serial port {0}".format(serial_port))
        return

    finish_socket_thread = False
    id = 0

    print("Reading data from serial port '{0}'".format(serial_port))
    print("")

    th_socket = Thread(target=socket_thread, args=(id, lambda: finish_socket_thread))
    th_socket.start()

    reboot = False

    while 1:
        try:
            if not ser:
                raise Exception("Serial port not assigned")

            barcode = read_serial_port(ser)
            bclean = barcode.strip()
            if bclean == "quit" or bclean == "exit" or bclean == "bye":
                print("Exit requested. Ending process.")
                break
            add_barcode(bclean)
        except Exception as e:
            log_error("Reading serial port. Exception: '{0}'".format(e))
            ser = reopen_serial_port(ser)
            if not ser:
                log_error("Trying to reopen serial port '{0}'".format(serial_port))
                if _AUTO_REBOOT:
                    reboot = True
                    break

    finish_socket_thread = True
    close_serial_port(ser)
    dump_list()

    print("")
    print("Cleaning GPIO")
    GPIO.cleanup()

    print("")
    print("Finishing main thread.")

    if reboot:
        reboot_device()


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


def close_serial_port(ser):
    if isinstance(ser, serial.Serial):
        if ser.is_open:
            ser.close()


def open_serial_port():
    print("Opening serial port '{0}'".format(serial_port))
    connected = False
    attempts = 0

    while not connected and attempts < _MAX_SERIAL_RETRIES:
        try:
            ser = serial.Serial(serial_port, 9600, timeout=1)
            connected = ser.is_open
        except Exception:
            attempts += 1
            time.sleep(2)  # Wait prior to attempt to open the port once again

    if connected:
        print("Port '{0}' opened successfully".format(ser.name))
        return ser
    else:
        log_error("Unable to open serial port '{0}'".format(serial_port))
        return False


def reopen_serial_port(ser):
    print("Reopening serial port")
    close_serial_port(ser)
    return open_serial_port()


def read_serial_port(ser):
    if isinstance(ser, serial.Serial):
        # In case the CPU usage is really high we can replace the serial.readline() by our own implementation
        # return sreader.ReadLine(ser).readline().decode()
        return ser.readline().decode()
    else:
        return ""


def send_to_socket(barcode):
    if barcode.strip() == "":
        return True

    connected = False
    retries = 0
    client_socket = None

    while not connected and retries < _MAX_SOCKET_RETRIES:
        try:
            print("Sending barcode '{2}' to {0}:{1}".format(
                host, port, barcode))
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
