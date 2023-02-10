# Serial port to network socket service for Raspberry Pi
The script written in Python is designed to maintain an open serial port for data retrieval and then transfer the 
collected data to an IPv4 address and port.

The source serial port and destination IP:port settings is obtained from the configuration file named `sts.conf`.

### Server requirements
* Python 3.x (`python --version`)
* GIT client
* Python pip library manager

## SETUP

### Clone this project using git command line tools
```shell
git clone the_repo /home/pi/sts
```

### Install Python libraries
Option A) By using `python`:
```shell
python -m pip install configParser
python -m pip install pyserial
python -m pip install RPi.GPIO
```
Option B) Using `pip`:
```shell
sudo pip install configParser
sudo pip install pyserial
sudo pip install RPi.GPIO
```
NOTE: Please be advised that a "sudo" installation is mandatory when running STS as a "daemon" service.

Option C) For Debian based OS it is also possible to install the dependencies using `apt`:
```shell
sudo apt-get update

sudo apt-get -y install python-configparser
sudo apt-get -y install python-serial
sudo apt-get -y install python-rpi.gpio
```

### Duplicate the "sts.conf.dev" file and rename the copy as "sts.conf".

```shell
cp sts.conf.dev sts.conf
```
Configure the sts.conf file to indicate the appropriate IP address (and, if necessary, the serial port).

#### Sample configuration file
The `.conf` file contents should look like:
```text
[hostinfo]
write.ip=192.168.1.103
write.port=15010
read.port=/dev/ttyACM0
read.end_char=13
```

> NOTE: Since this code was written for a specific use case, the serial port basic configuration (9600 bauds) is currently hardcoded.

> WARNING: Configure the read.end_char to the appropriate ASCII code representing the End of Transmission character (ETX) transmitted by the serial port.

### Execute the tool / service
For proper functionality, a remote computer with the IP 'write.ip' should be actively listening on the designated port 'port'.

```shell
python sts.py
```
or
```shell
sh sts_service.sh
```

## Optional: DAEMONIZE THE SCRIPT
```shell
sudo chmod +x sts_service.sh
sudo cp /home/pi/sts/init.d/sts /etc/init.d
sudo chmod +x /etc/init.d/sts
```
It is now necessary to update the .rc boot scripts to allow the *sts* service to be executed during system boot.
```shell
sudo update-rc.d sts defaults
```
Finally, and optionally, just for testing the *sts* service without requiring to reboot the system:
```shell
sudo systemctl daemon-reload
```

From now on, it is possible to control the script using:
```shell
sudo /etc/init.d/sts start
or
sudo service sts start
```
```shell
sudo /etc/init.d/sts stop
or
sudo service sts stop
```
```shell
sudo /etc/init.d/sts restart
or
sudo service sts restart
```
```shell
sudo /etc/init.d/sts status
or
sudo service sts status
```

### Stopping the service manually
```text
If it has been executed manually press *control+z*
```
```shell
ps aux |grep -i sts.py  (to get the process ID)
kill -9 ID
```

## TESTING AND TROUBLESHOOTING
It is possible to conduct a test of the service by using keyboard inputs to simulate barcode scans instead of using the 
serial port, allowing you to verify communication with the remote socket.
```shell
python sts_keyboard.py
```

When the remote computer is not available or not responding, the script `server_test.py` emulates a socket server 
listening to the same port. It just dumps/echoes to the console whatever it receives.

For this testing, it is necessary to set the client (such as 'sts.py' or 'sts_keyboard.py') to point to the local IP 
address of 127.0.0.1.
```shell
python server_test.py
```
