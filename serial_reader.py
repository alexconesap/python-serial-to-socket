# Class ReadLine
# Reads data from a given serial port object and returns it as a simple string.
#
# Example of use:
#   import serial
#   import serial_reader as sreader
#
#   ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
#   return sreader.ReadLine(ser).readline().decode()
class ReadLine:
    def __init__(self, serialobj):
        self.buffer = bytearray()
        self.serialobj = serialobj

    def readline(self):
        i = self.buffer.find(b"\n")
        if i >= 0:
            r = self.buffer[:i+1]
            self.buffer = self.buffer[i+1:]
            return r
        while True:
            i = max(1, min(2048, self.serialobj.in_waiting))
            data = self.serialobj.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buffer + data[:i+1]
                self.buffer[0:] = data[i+1:]
                return r
            else:
                self.buffer.extend(data)
