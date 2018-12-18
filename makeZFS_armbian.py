import os
import sys
import time
#from datetime import datetime
#from datetime import timedelta

def setupEnvironments():
	log_enter_func(sys._getframe().f_code.co_name, True)

	print("# Setup Environments")

	cmds = ["sudo apt-get update", 
					"sudo apt-get -y install build-essential autoconf libtool gawk alien fakeroot autogen",
					"sudo apt-get -y install gdebi wget curl flex bison dkms",
					"sudo apt-get -y install zlib1g-dev uuid-dev libattr1-dev libblkid-dev libselinux-dev libudev-dev libaio-dev",
					"sudo apt-get -y install parted lsscsi ksh libssl-dev libelf-dev",
					"sudo apt-get -y install python",
			   ]
	for cmd in list(cmds):
		run_cmd(cmd)

	return 0

# process /usr/src/linux-headers-$(uname -r)/
def procLinuxheaders(parent_path):
	log_enter_func(sys._getframe().f_code.co_name, True)

	print("# Process \"/usr/src/linux-headers-$(uname -r)/\"")

	ver = os.popen("uname -r").read().strip()
	linux_headers_path = parent_path + "/linux-headers-" + ver
	if (modifyMakefile(linux_headers_path) == 0):
		cmd = "cd " + linux_headers_path + " && sudo make scripts"
		run_cmd(cmd)
		return 0

	return 1

# modify scripts/Makefile
def modifyMakefile(workspace_path):
	log_enter_func(sys._getframe().f_code.co_name)

	target_file = workspace_path + "/scripts/Makefile"
	print("# Modify file: " + target_file)
	if (not os.path.isfile(target_file)):		
		print("File path \"{}\" does not exist.".format(target_file))
		return 1

	fp = open(target_file, "r")
	file_contents = fp.readlines()
	fp.close()

	target = False
	list_contents = []
	for fLine in list(file_contents):
		if ("subdir-$(CONFIG_SECURITY_SELINUX) += selinux" in fLine and fLine.lstrip()[0] == 's'):
			target = True
			fLine = "#" + fLine
			print("Found target! commant out: \"{}\"".format(fLine.strip()))
		list_contents.append(fLine)

	global real_runing

	if (target and real_runing == True):
		print("Write file")
		fp = open(target_file, "w+")
		fp.writelines(list(list_contents))
		fp.close()

	return 0

def buildZFS_SourceCode():
	log_enter_func(sys._getframe().f_code.co_name, True)

	print("# Build ZFS source code")
	workspace_path = os.popen("pwd").read().strip() + "/zfs_autobuild_" + str(int(time.time()))
	print("Workspace path: " + workspace_path)

	os.mkdir(workspace_path)
	os.chdir(workspace_path)

	run_cmd("sudo git clone https://github.com/zfsonlinux/zfs")

	cmds = ["sudo ./autogen.sh && sudo ./configure --with-linux=/usr/src/linux-headers-$(uname -r) --with-linux-obj=/usr/src/linux-headers-$(uname -r)",
					"sudo make -s -j$(nproc) && sudo make -j1 pkg-utils deb-dkms",
					"for file in lib*.deb; do sudo gdebi -q --non-interactive $file; done",
					"for file in zfs*.deb; do sudo gdebi -q --non-interactive $file; done",
			   ]
	for cmd in list(cmds):
		run_cmd("cd zfs && " + cmd)

	return 0

def installZFS():
	log_enter_func(sys._getframe().f_code.co_name, True)

	print("# Install ZFS")

	dkms_zfs_path = "/var/lib/dkms/zfs/"
	if (os.path.exists(dkms_zfs_path) == 0):
		return 1
	zfs_ver = os.popen("cd " + dkms_zfs_path + " && ls -d1 -p -A " + "*").read().strip()
	end_idx = zfs_ver.find("/")
	dbg_print(zfs_ver + ", " + str(end_idx))
	if (end_idx < 2):
		return 2

 	if (zfs_ver[end_idx] != "/"):# or zfs_ver[end_idx + 1] != "\n"):
		print("No zfs vertion direction founded")
		return 3

	cmds = ["sudo dkms install zfs/" + zfs_ver[0:end_idx],
					"sudo modprobe zfs",
					"dkms status",
					"sudo systemctl enable zfs-import-scan",
					"sudo systemctl enable zfs-import-cache",
					"sudo systemctl enable zfs-import.target",
					"sudo systemctl enable zfs.target",
					"sudo systemctl enable zfs-mount",
					"sudo systemctl enable zfs-share",
					"sudo systemctl enable zfs-zed",
	
					"sudo systemctl start zfs-import-scan",
					"sudo systemctl start zfs-import-cache",
					"sudo systemctl start zfs-import.target",
					"sudo systemctl start zfs.target",
					"sudo systemctl start zfs-mount",
					"sudo systemctl start zfs-share",
					"sudo systemctl start zfs-zed",
					"cd / && sudo systemctl --no-pager --failed status zfs*",
					"systemctl list-unit-files | grep zfs",
			   ]
	for cmd in list(cmds):
		run_cmd(cmd)

	return 0

real_runing = True
def run_cmd(cmd):
	global real_runing

	print("  * " + cmd)
	if real_runing == True:
		os.system(cmd)

dbg_mode = False
def dbg_print(string):
	global dbg_mode

	if (dbg_mode == True): print("---> Dbg: " + string)

func_log_indent = 0
current_level = 0
def log_enter_func(func_name, root_level = False):
	global func_log_indent, current_level

	if (root_level):
		func_log_indent = 1
		current_level += 1
		sys.stdout.write("\n")
	else:
		func_log_indent += 1

	sys.stdout.write("Level [" + str(current_level) + ".")
	sys.stdout.write(str(func_log_indent) + "]: ")

	i = 0
	for i in range(func_log_indent):
		sys.stdout.write("-")

	print("---> " + func_name + "()")
	return 0

def main():
	global real_runing, dbg_mode

	ret = 0

	real_runing = True
	if (len(sys.argv) >= 2):
		real_runing = False

	dbg_mode = True

	print("runing mode: " + str(real_runing))

	if (real_runing == True):
		os.system("sudo rm -rf ~/zfs_autobuild*")
		os.system("sudo rm -rf /usr/src/zfs_autobuild*")
		os.system("sudo rm -rf /var/lib/dkms/zfs_autobuild*")
		os.system("sudo rm -rf /var/lib/dkms/zfs")

	ret |= setupEnvironments()
	if (ret == 0):
		# Proc /usr/src/linux-headers-xxx
		ret |= procLinuxheaders("/usr/src")
		if (ret == 0):
			# Build ZFS source code
			ret |= buildZFS_SourceCode()
			if (ret == 0):
				# Install ZFS images
				ret |= installZFS()
				print("ret = " + str(ret))
				
	if (ret == 0):
		print("All are done! It's better to restart system before use ZFS")
	else:
		print("Looks like there have some issues, please confirm it.")

	return ret

if (__name__ == "__main__"):
	print("|======================================================================|")
	print("|               <<Setup ZFS file system on Armbian>>              v1.0 |")
	print("|                                               Author: Rainforest.Lee |")
	print("|                                                           2018/11/15 |")
	print("|======================================================================|\n")
	print("=== Enter " + __name__ + "() ===")
	print("current Python version is {}.{}".format(sys.version_info.major, sys.version_info.minor))
	ret = main()
	print("=== Exit " + __name__ + "() ===")
	#return ret

print("The End")

