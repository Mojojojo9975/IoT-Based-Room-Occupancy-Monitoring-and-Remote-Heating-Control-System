# IoT-Based Room Occupancy Monitoring and Remote Heating Control-System
The final project for "Internet of Things 52104S-3006" course at University of Oulu is presented here. In this project, occupancy count is estimated at edge. The user can monitor the sensors readings and calculated numbers of residents in real-time.

## Devices
* Raspberry Pi 3
* Raspberry Pi Pico W
* Raspberry Pi camera module
* RS-485 CAN HAT for Raspberry Pi 3
* Pico- 2CH-RS485 Hat for raspberry pi pico
* compatible 4G/5G USB dongle with Raspbian OS
* Magnetic door switch
* LED and 10k resistor
* DB9 cable
* BMP 280
* HC_SR04
## Dependencies

* LabVIEW 2024 Q3 with the following packages and toolkits:
  * [Hobbyist version 2024 Q3](https://www.ni.com/en/support/downloads/tools-network/download.labview-hobbyist-toolkit.html?srsltid=AfmBOootf6Z0s5w6TBujDSQhxd81qou_WAUbxogZ993ae2nn6GK9WtHZ#569351)
  * NI-VISA
  * [MQTT Broker 4.0.2.17 by G Open Source Project for LabVIEW](https://www.vipm.io/package/labview_open_source_project_lib_mqtt_broker/)
  * MQTT Client 4.0.0.15 by G Open Source Project for LabVIEW
  * MQTT Connection 4.0.0.25 by G Open Source Project for LabVIEW
  * MQTT Control Packets 3.1.4.10 by G Open Source Project for LabVIEW
  * MQTT LocalQueue Connection 4.0.0.5 by G Open Source Project for LabVIEW
  * MQTT TCP Connection 4.0.0.7 by G Open Source Project for LabVIEW
  * MQTT Websockets Connection 4.0.0.10 by G Open Source Project for LabVIEW
* [Raspbian with LabVIEW pre installed](https://github.com/LVMakerHub/LINX/wiki/installing-an-image-with-LabVIEW-pre-installed)

## Raspbian Configuration for Raspberry Pi 3:
* Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/) or other similar programs such as [Rufus](https://rufus.ie/en/) to fomat Raspberry Pi
* Install a bootable Raspbian OS with the appropriate LabVIEW version preinstalled
* Reinsert the memory to PC and look for a file named cmdline open it with a text editor such as Notepad plus and add the following at the end of string. It gives an static IP to the Raspberry Pi:
  `ip=192.168.1.99::192.168.1.50:255.255.255.0:rpi:eth0:off`
  in which 192.168.1.99 is the configured static IP address for raspberry Pi and 192.168.1.50 is the IP address which Raspberry Pi expects as a connecting device (for example your PC) as gateway

**Note**: if you are using Compute Raspberry Pi models, you will need rpiboot tool which is installed with Raspberry Pi imager
* Plug in the Raspberry Pi with its memory and connect it to the PC with Ethernet cable
* Configure your static IP in your PC same as 192.168.1.50
* use this command  `sudo nmtui` to remove the extra Ethernet 0 interface and edit the configuration for the other one:
  * Tick **Automatically connect** and also **Never use this nethwork as default router** options
* update the installed packages with `sudo apt-get update` and `sudo apt-get upgrade`
* Change the cmdline file again ` sudo nano /boot/firmware/cmdline.txt` and remove the command that was added previously
* Install camera stack with `sudo apt install -y libcamera-apps libcamera-dev`
* Install Opencv with `sudo apt install -y libopencv-dev`
* [Download the MobileNet-SSD model](https://github.com/nikmart/pi-object-detection)
* compile the cpp file `g++ -o udp_person_counter udp_person_counter.cpp $(pkg-config --cflags --libs opencv4)`
* To make the execute file running on background as start up you can use `udp_person_counter.service`
* To create an automatic SSH tunnel to the server use `reverse-ssh-tunnel.service` but we also need to create SSH key and copy it to your private server (we use the SSH tunnel to transfer captured images)
* Use the following commands to activate these services:
  * `sudo systemctl daemon-reload`
  * `sudo systemctl enable udp_person_counter.service`
  * `sudo systemctl enable reverse-ssh-tunnel.service`
  * `sudo systemctl start udp_person_counter.service`
  * `sudo systemctl start reverse-ssh-tunnel.service`
* To deploy LabVIEW vi as startup you need to open IoT project right click on build specification -> new -> Real-Time Application
  * in **Source File Section** choose main_v6.vi as startup VI click on build buttom
  * then you can deploy it
## Pico Configuration:
* Setup MicroPython on Raspberry Pi Pico W
* create main.py and use the given main.py script
## Hardware setup:
* on Raspberry Pi Pico W use these pins:
  * Pin 4 -> HC_SR04 echo
  * Pin 5 -> HC_SR04 Trig
  * Pin 40 -> HC_SR04 Vcc
  * Pin 38 ->  HC_SR04 GND
  * Pin 36 ->  BMP 280 Vcc
  * Pin 33 -> BMP 280 GND
  * Pin 27 -> BMP 280 Scl
  * Pin 27 -> BMP 280 SdA
  * Pin 38 ->  magnetic switch
  * Pin 19 ->  magnetic switch
  * use A, B ,G pins for connecting to Pin number 1,2 ,5 in DB9 cable accordingly
* on Raspberry Pi 3 use these pins:
   * Pin 6 -> DB9 pin 5
   * Pin 13 and 9 -> to LED and resistors in series
 ## Private server configuration:
For this project Ubuntu 22 was installed in the private server
* install Hive MQTT broker:
  * `sudo apt update`
  * `sudo apt install git`
  * `mkdir broker && cd broker`
  * Download [HiveMQ broker](https://github.com/hivemq/hivemq-community-edition/releases)
  * 'curl -L -o hivemq-ce-2024.9.zip https://github.com/hivemq/hivemq-community-edition/releases/download/2024.9/hivemq-ce-2024.9.zip'
  * `sudo apt update && sudo apt install unzip`
  * `unzip hivemq-ce-2024.9.zip`
  * Download [Java Development Kit](https://www.oracle.com/java/technologies/javase/jdk23-archive-downloads.html)
  * 'cd Java/'
  * `sudo dpkg -i jdk-23_linux-x64_bin.deb`
  * `./hivemq-ce-2024.9/bin/run.sh`
  * To make this .sh run in background, make a systemd service:
  * ` sudo nano /etc/systemd/system/hivemq.service`
  * Use given **hivemq.service** configuration
  * `sudo systemctl daemon-reload`
  * `sudo systemctl enable hivemq.service`
  * `sudo systemctl start hivemq.service`

## Tests for Evaluating maximum throughput:
 * For checking the maximum throughput over RS-485 link you can use test.py file located in Pico/Test and also use test.vi in RPI/test
 * For checking the maximum throughput over Wi-Fi with UDP tranmission, you can use test2.py file located in Pico/Test and also use test2.vi in RPI/test
  * Change SSID, PASSWORD according to your Wi-Fi configuration
  * change UDP_TARGET_IP based on your Raspbery Pi 3 IP adderess you can check it with `ifconfig`
