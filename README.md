makeZFS_armbian.py is a tool which make ZFS on your armbian linux (64 bit) automatically.

# Usage:
```
sudo add-apt-repository ppa:jonathonf/zfs
sudo apt update
git clone https://github.com/nathmo/makeZFS_armbian
cd makeZFS_armbian
sudo python3 makeZFS_armbian.py
apt install zfs-dkms zfs-zed zfsutils-linux
```
now you should be able to use ZFS on armbian

# Grand scheme of thing
this script is used to install ZFS on a rockpro64 used as a low power NAS / server for domestic application

if you want to replicate the whole NAS and not juste ZFS use the following insctruction

## Initial setup
you will need :

* a rockPro64
* a power supply (i used a standard computer PSU to power the hdd and the rockPro64)
* a bunch of HDD (6x 2Tb in my case)
* a fan with a molex connector (or two)
* a case
* a good SD card and optionnally a USB HDD
* a few MOLEX cable stub to make a connector for the RockPro

here is how it looks like
![photo_2022-10-08_00-29-31](https://user-images.githubusercontent.com/15912256/194671253-f7bea648-9d09-4158-951b-4457fcbe93b9.jpg)
![photo_2022-10-08_00-29-32](https://user-images.githubusercontent.com/15912256/194671248-d3d5a9d1-f073-44bc-b879-51aa8bf9bf02.jpg)
![photo_2022-10-08_00-29-31 (3)](https://user-images.githubusercontent.com/15912256/194671251-cf19e09b-48c8-463a-979e-5322d387bdf1.jpg)
![photo_2022-10-08_00-29-31 (2)](https://user-images.githubusercontent.com/15912256/194671252-63074964-6d42-43d8-bb55-7aa28cb358b4.jpg)
(it only draw 55 Watt with every disk spinning, probably less than that usually)

## Flash RockPro64 USB Boot
follow this guide to flash the sd card to update the SPI flash.
if you plan to run the OS from the sd card directly you can skip this step
https://wiki.pine64.org/index.php/NOOB#Flashing_u-boot_to_SPI_Flash

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

## setup OS
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

## install ZFS and cockpit
reconnect over ssh once the reboot is done

then install zfs and cokpit (give you a nice web dashboard under https://192.168.YYY.XXX:9090/
![image](https://user-images.githubusercontent.com/15912256/194674108-69b36efa-8e62-4a1b-9cae-8dffc15cb7f5.png)
(here is the cockpit interface)

```
sudo su
apt install curl
apt install cockpit cockpit-pcp
sudo add-apt-repository ppa:jonathonf/zfs
apt update
git clone https://github.com/nathmo/makeZFS_armbian
cd makeZFS_armbian
python3 makeZFS_armbian.py
apt install zfs-dkms zfs-zed zfsutils-linux
sudo apt-get -y install linux-headers-current-rockchip64
apt install samba nfs-kernel-server
apt install docker-compose
sudo modprobe usbcore autosuspend=-1
sudo reboot now
```


## create your ZFS pool

```
sudo fdisk -l
sudo zpool create -m /pool storagearray raidz2 /dev/sda /dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf
sudo zpool status
```
your pool is automatically mounted under /pool but you can change the location
raidz2 use two drive for parity bit. you can use use raid1 for only one parity bit

## setup docker and portainer
docker allow you to run container, portainer is a nice web page to manage your portainer. its more user friendly than the shell at first

```
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
systemctl status docker
sudo docker run -d -p 8000:8000 -p 9000:9000 -p 9443:9443 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:latest
```

there is even a way to directly have your docker volume on the zfs array but i dont know how yet
## configure Samba and NFS

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
