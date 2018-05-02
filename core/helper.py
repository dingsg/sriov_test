from sriov_test.core.config import *
from sriov_test.utils.utils import *
import socket
import netifaces

def load_gim():
    cmd = 'insmod ' + conf_gim() + 'gim-api/gim-api.ko'
    run(cmd)
    cmd = 'insmod ' + conf_gim() + 'sriov_drv/gim.ko'
    run(cmd)

def unload_gim():
    run('rmmod gim')
    run('rmmod gim-api')

def create_test_images():
    cmd = 'qemu-img create -f qcow2 -b '
    cmd = cmd + conf_base_image() + ' ' + conf_tmp_images_dir()
    for i in range(16):
        run(cmd + '/test_%x.qcow2' % i)

def remove_test_images():
    cmd = 'rm -rf ' + conf_tmp_images_dir()
    run(cmd)
