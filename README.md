this repo contains instruction to make a descent NAS / home server using a rock pro 64 as it's heart.

# Table of Contents
[Case assembly](#mechanical-assembly-of-the-case)
[Hardware requirement](#mechanical-assembly-of-the-case)
[Software setup](#mechanical-assembly-of-the-case)
[More pictures](#mechanical-assembly-of-the-case)
[about the case](#mechanical-assembly-of-the-case)

# Mechanical assembly of the case
i used white glue. it works. the last pannel is just held in place with the tight clearance. might work on a hinge later for easy access
![photo_2022-10-08_00-29-31](https://user-images.githubusercontent.com/15912256/194671253-f7bea648-9d09-4158-951b-4457fcbe93b9.jpg)

# Hardware requirement
you will need :

* a rockPro64
* a power supply (i used a standard computer PSU to power the hdd and the rockPro64)
* a bunch of HDD (6x 2Tb in my case)
* a fan with a molex connector (or two)
* a case (remind me to release the file or use a normal computer case)
* a good SD card or optionnally a USB HDD
* a few MOLEX cable stub to make a connector for the RockPro

# Software setup

## Flash RockPro64 USB Boot
follow this guide to flash the sd card to update the SPI flash.
if you plan to run the OS from the sd card directly you can skip this step
https://wiki.pine64.org/index.php/NOOB#Flashing_u-boot_to_SPI_Flash
here is what it say :

This may be the simplest method of flashing u-boot to SPI. Download a dedicated image labelled u-boot-flash-spi.img.xz from [ayufan's github|https://github.com/ayufan-rock64/linux-u-boot/releases] and flash it to a microSD card, the same as you would with any OS image (to learn how to flash OS images to microSD please follow steps outlined in Section 3.

Having flashed the image follow these steps:

    Insert the SD into the ROCK64
    Remove all other peripherals from the board
    Make sure that the eMMC module is disconnected from the board
    Apply power to the ROCK64
    Wait (few seconds) until the the LEDs on the board will blink continually
    Power off the board.

The board is now ready to boot from USB 2.0 storage. 

(if you use a USB 3.0 UDD, try to use the USB 3.0 port with a USB 2.0 only cable extender to a USB3.0 HDD as this port allow more current to be drawn but saddly USB3.0 dont seems to be supported as a boot medium so the USB 2.0 extender force the HDD to fallback to USB 2.0)

## Install OS
install armbian (jammy 22.08.1) on the sd card or the USB HDD depending of what you want to use
to do so : download and extract the image for your board
https://www.armbian.com/rockpro64/
(download jammy, CLI only)

on linux you can run this from the folder where you downloaded the image (change sdX by the drive shown with lsblk)
```
lsblk
sudo dd of=/dev/sdX if=Armbian_22.08.1_Rockpro64_jammy_current_5.15.63.img bs=1M status=progress
```
on windows you can just use [RUFUS](https://rufus.ie/fr/)

once you are done you can optionnally extend the partiion to use your whole drive (use GParted on linux)
or you can just wait for it do be done automatically at first boot but its reallly slow

then you insert the boot devince in the rockpro64

## OS setup
find the IP your DHCP gave to the board (use nmap, zenmap, the admin page or your routeur or whatever)
once done : 
```
ssh root@192.168.YYY.XXX
```
(or use putty on windows)
the user is root and the password is 1234
once logged in you are prompted to change the password and setup the user account

I used bash and set the user to ubuntu

then you can run
```
armbian-config
```
and set the hostname to whatever you like and then change the IP address to a static one. (it crash the ssh connection. it's normal, start a new one with the new IP)

```
ssh ubuntu@192.168.YYY.XXX
```
I recommend adding your public sh key so taht you dont need a password to login :
```
mkdir .ssh
nano .ssh/authorized_keys
```
paste the content of .ssh/id_rsa.pub of your machine to the authorized file there (from your linux machine. you can find out how to do it with putty if you want)
once done you can update and reboot : 
```
sudo apt update
sudo apt upgrade
sudo reboot now
```
if you choose to run from a SD card : use Log2RAM to reduce wear :
```
echo "deb [signed-by=/usr/share/keyrings/azlux-archive-keyring.gpg] http://packages.azlux.fr/debian/ bullseye main" | sudo tee /etc/apt/sources.list.d/azlux.list
sudo wget -O /usr/share/keyrings/azlux-archive-keyring.gpg  https://azlux.fr/repo.gpg
sudo apt update
sudo apt install log2ram
```
## test the hardware for faulty block
#### RAM TEST
do it quickly after receinving your board as you only have 30 day to report thoses problem to pine and get a new board for free in case of error.
test the RAM for faulty block
```
sudo apt-get install memtester
```

```
sudo memtester 3300 5
```

#### HDD/SD/USB test
dont buy them on aliexpress is usually a good start...

## install ZFS and cockpit
reconnect over ssh once the reboot is done

then install zfs and cokpit (give you a nice web dashboard under https://192.168.YYY.XXX:9090/


```
sudo su
apt install curl
apt install cockpit cockpit-pcp
sudo apt install zfs-dkms zfsutils-linux
sudo apt-get -y install linux-headers-current-rockchip64
apt install samba nfs-kernel-server
apt install docker-compose
sudo modprobe usbcore autosuspend=-1
udo systemctl status sleep.target suspend.target hibernate.target hybrid-sleep.target
sudo reboot now
```

![image](https://user-images.githubusercontent.com/15912256/194674108-69b36efa-8e62-4a1b-9cae-8dffc15cb7f5.png)
(here is the cockpit interface)

## create your ZFS pool

```
sudo fdisk -l
sudo zpool create -m /pool storagearray raidz2 /dev/sda /dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf
sudo zpool status
```
your pool is automatically mounted under /pool but you can change the location
raidz2 use two drive for parity bit. you can use use raid1 for only one parity bit

if you aldready have a ZFS pool from a previous install you can import it with 
```
sudo zpool import storagearray -f
```
## setup docker and portainer
docker allow you to run container, portainer is a nice web page to manage your portainer. its more user friendly than the shell at first
here we create a volume on the ZFS array for portainer and then launche the portainer container
```
sudo su ubuntu
cd /pool
mkdir container
cd container
mkdir portainer
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
systemctl status docker
sudo docker run -d -p 8000:8000 -p 9000:9000 -p 9443:9443 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v /pool/container/portainer:/data portainer/portainer-ce:latest
```

there is even a way to directly have your docker volume on the zfs array but i dont know how yet
## configure Samba, syncthings and NFS

```
sudo curl -o /usr/share/keyrings/syncthing-archive-keyring.gpg https://syncthing.net/release-key.gpg
echo "deb [signed-by=/usr/share/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" | sudo tee /etc/apt/sources.list.d/syncthing.list
sudo apt-get update
sudo apt-get install syncthing
systemctl enable syncthing@ubuntu.service
systemctl start syncthing@ubuntu.service
systemctl status syncthing@ubuntu.service
nano /home/ubuntu/.config/syncthing/config.xml
```
modifiy this line to expose you local IP : 
```
<address>192.168.1.10:8384</address>
```
save and exit
```
sudo cp /etc/samba/smb.conf /etc/samba/smb.orig
sudo nano /etc/samba/smb.conf

```

```
## NAS Samba Configuration

[global]
  workgroup = KTZ
  server string = MYNAS
  security = user
  guest ok = yes
  map to guest = Bad Password

  log file = /var/log/samba/%m.log
  max log size = 50
  printcap name = /dev/null
  load printers = no

# Samba Shares

[storage]
  comment = Storage on epsilon
  path = /pool/NAS
  browseable = yes
  read only = no
  guest ok = yes
  
  
```
and finally
```
systemctl restart smbd

```

if you're happy with it you can stop there. if you keep reading you will setup a VPN server to remotely connect to your network and a dynDNS in case your IP is not static

```
sudo curl -L https://install.pivpn.io | sudo bash
```
choose what you want. i personnaly went with wireguard on the default port and openDNS as the DNS server.
then reboot. you can add configuration with
```
pivpn -a
```
git a name. you can either use 
```
pivpn -qr
```
to get a QR code that you can scan or you can 
```
cat /home/ubuntu/configs/*.conf
```
and you can import that in a text file on your device and import it into wireguard vpn client.


then you might want to setup a dynDNS if you own a domain from some company like OVH and you dont have a static IP.
what it does is basically tell the OVH DNS server that your domain should point to this IP address. this IP address being the one your ISP gave you.
and if it change the script update it automatically.

```
sudo apt-get install ddclient
sudo apt install libio-socket-ssl-perl
```
then you can enter the following value given by your registrat (OVH for me)
![image](https://user-images.githubusercontent.com/15912256/197188539-fc47749d-6dee-4c07-af22-b387624b7fdb.png)

```
Dynamic DNS service provider:other
Dynamic DNS update protocol : dyndns2
Dynamic DNS server : www.ovh.com
Username for dynamic DNS service: OVH dynDNS username
Password for dynamic DNS service: OVH dynDNS passowrd
Re-enter password to verify: OVH dynDNS password (again)
```
you are all set. your domain name should point to your home IP address.


# final result

here is how it looks like
![photo_2022-10-08_00-29-31 (3)](https://user-images.githubusercontent.com/15912256/194671251-cf19e09b-48c8-463a-979e-5322d387bdf1.jpg)
![photo_2022-10-08_00-29-31 (2)](https://user-images.githubusercontent.com/15912256/194671252-63074964-6d42-43d8-bb55-7aa28cb358b4.jpg)

(it only draw 55 Watt with every disk spinning, probably less than that usually)

# More on the case 

the case is made to be versatil and accomodate up to 7 board or HDD (maybe double of that for small SBC)
here is a sample of a few different configuration 
![image](https://user-images.githubusercontent.com/15912256/196444699-1ef1e6ca-c69f-47ab-9ae8-2a44b5a70875.png)
