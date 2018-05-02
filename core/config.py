from sriov_test.utils.utils import *
from ConfigParser import *
import socket
import netifaces
import os

config_file = abs_path(__file__) + '/../sriov_test.conf'
sriov_config = RawConfigParser()
sriov_config.read(config_file)


def save_conf():
    with open(config_file,'wb+') as f:
        sriov_config.write(f)


class ConfigException(Exception):
    def __init__(self, err):
        super(ConfigException, self).__init__(err +'@'+ config_file)


def conf_base_image():
    try:
        base_image = sriov_config.get('guest', 'base_image')
        if os.path.isfile(base_image):
            return base_image
        else:
            raise Exception()
    except:
        raise ConfigException("You must indicate the base image")


def conf_user():
    while True:
        try:
            user = sriov_config.get('guest', 'user')
            if user == '':
                raise Exception()
            return user
        except:
            raise ConfigException("Please set the user of guests")

def conf_password():
    while True:
        try:
            passwd = sriov_config.get('guest', 'password')
            if passwd == '':
                raise Exception()
            return passwd
        except:
            raise ConfigException("Please set the password of guests")


def conf_device_id():
    while True:
        try:
            did = sriov_config.get('host', 'device_id')
            if did == '':
                raise Exception()
            return did
        except:
            raise ConfigException("Please configure the device ID")


def conf_interface():
    while True:
        try:
            interface = sriov_config.get('host', 'interface')
            if interface == '':
                raise Exception()
            return interface
        except:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 80))
            (addr, tmp) = sock.getsockname()

            for each in netifaces.interfaces():
                nic = netifaces.ifaddresses(each)
                if not nic.has_key(socket.AF_INET):
                    continue
                if addr in nic[socket.AF_INET][0]['addr']:
                    sriov_config.set('host','interface',each)
                    save_conf()
                    break


def conf_gim():
    try:
        gim = sriov_config.get('host', 'gim')
        if os.path.isdir(gim):
            return gim
        else:
            raise Exception()
    except:
        raise ConfigException("You must set the gim directory")
        

def conf_bridge_name():
    while True:
        try:
            bridge = sriov_config.get('host', 'bridge_name')
            if bridge == '':
                raise Exception()
            return bridge
        except:
            sriov_config.set('host','bridge_name','sriov-br')
            save_conf()


def conf_tmp_images_dir():
    while True:
        try:
            path = sriov_config.get('host', 'working_dir') + '/images/'
            if os.path.isdir(path):
                return path
            else:
                raise Exception()
        except:
            run('mkdir -p ' + path)

