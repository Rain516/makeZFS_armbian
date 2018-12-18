makeZFS_armbian.py is a tool which make ZFS on your armbian linux (64 bit) automatically.

Usage:
sudo python makeZFS_armbian.py


By The Way:
currently, zfsonlinux 0.8.x still in development stage.
I did test: so far looks like that the ZFS 0.8.x is ONLY matched on Xenial 16.04 x64. 
On Bionic 18.04 x64, I found that the cache of ZFS 0.8.x causes ZFS pool LOST after armbian reboot.

