from sriov_test.utils.utils import *
from sriov_test.utils.forward import *
from multiprocessing.pool import ThreadPool
from config import *
import paramiko
import libvirt
import netifaces
import socket
import time
import os

def libvirt_wrapper(method):
    def wrapper(*args):
        args[0].conn = libvirt.open()
        r = method(*args)
        try:
            args[0].conn.close()
        except:
            pass
        return r
    return wrapper

class SriovHost(object):
    def __init__(self):
        self.net_xml = abs_path(__file__) + '/xmls/network.xml'
        self.vm_xml = abs_path(__file__) + '/xmls/template.xml'
        self.vfs = list_vfs(conf_device_id())
        try:
            self.conn = libvirt.open()
        except:
            assert False
        self.conn.close()
        self.get_bridge()

    def run(self, cmd, nohup=None):
        if nohup:
            cmd = 'nohup ' + cmd + ' > nohup.out 2>&1 &'
        return run(cmd)

    @libvirt_wrapper
    def get_bridge(self):
        try:
            return self.conn.networkLookupByName(conf_bridge_name())
        except:
            with open(self.net_xml, 'r') as f:
                xmlstr = f.read()
                xmlstr = xmlstr.replace('INTERFACE', conf_interface())
                xmlstr = xmlstr.replace('NAME', conf_bridge_name())

            return self.conn.networkCreateXML(xmlstr)

    @libvirt_wrapper
    def create_guests(self, name, count):
        guests = []
        vms = []
        with open(self.vm_xml, 'r') as f:
            basexml = f.read()
        for each in range(count):
            xmlstr = basexml.replace('NAME', name)
            xmlstr = xmlstr.replace('BRIDGE', conf_bridge_name())
            xmlstr = xmlstr.replace('COUNT', '%x' % each)
            xmlstr = xmlstr.replace('BASEIMAGE', conf_base_image())
            xmlstr = xmlstr.replace('BUS', self.vfs[each]['bus'])
            xmlstr = xmlstr.replace('DEVICE', self.vfs[each]['device'])
            xmlstr = xmlstr.replace('FUNCTION', self.vfs[each]['function'])
            xmlstr = xmlstr.replace('IMAGEPATH', conf_tmp_images_dir())
            guest = SriovGuest(xmlstr)
            guest.create()
            guests.append(guest)
        for each in guests:
            each.wait_for_up()
        print "wait for up done"
        time.sleep(5)
        for each in guests:
            each.ssh_copy_id()
            each.attach()
        print "attach done"
        return guests

    @libvirt_wrapper
    def destroy_guests(self):
        vmids = self.conn.listDomainsID()
        for id in vmids:
            vm = self.conn.lookupByID(id)
            vm.destroy()

    @libvirt_wrapper        
    def list_guests(self):
        guests = []
        vmids = self.conn.listDomainsID()
        for id in vmids:
            vm = self.conn.lookupByID(id)
            guest = SriovGuest(vm.XMLDesc(), vm)
            guest.wait_for_up()
            guest.attach()
            guests.append(guest)
        return guests

    @libvirt_wrapper        
    def vnc_forward(self, guests=None):
        port = 9000
        params = []
        if guests == None:
            guests = self.list_guests()
        pool = ThreadPool(len(guests))
        for each in guests:
            params.append((port, each.ip, 5900))
            port = port + 1

        pool.map_async(forward, params)
        pool.close()
        while True:
            try:
                pass
            except KeyboardInterrupt:
                break
        pool.terminate()
        # pool.join()

class SriovGuest(object):
    def __init__(self, xmlstr, vm=None):
        self.xmlstr = xmlstr
        self.vm = vm

    def ssh_copy_id(self):
        ssh_setup(conf_user(), conf_password(), self.ip)

    @libvirt_wrapper
    def get_name(self):
        return self.vm.name()

    def attach(self, timeout=360):
        key_path = os.environ['HOME'] + '/.ssh/id_rsa'
        key = paramiko.RSAKey.from_private_key_file(key_path)
        self.ssh_conn = paramiko.SSHClient()
        self.ssh_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_conn.connect(hostname=self.ip, port=22, username=conf_user(), pkey=key)
        while timeout > 0:
            try:
                self.run('uname')
                return
            except:
                time.sleep(1)
                timeout = timeout - 1
                continue

    @libvirt_wrapper
    def get_ip(self):
        try:
            addresses = self.vm.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT)
            for each in addresses:
                if '192.168' in addresses[each]['addrs'][0]['addr']:
                    return addresses[each]['addrs'][0]['addr']
        except:
            raise Exception("Not ready")

    def wait_for_up(self, retry=360):
        while retry > 0:
            try:
                if self.get_ip():
                    self.ip = self.get_ip()
                    return
            except:
                retry = retry - 1
                time.sleep(1)
        raise Exception('wait_for_up timeout')

    def wait_for_down(self, retry=180):
        while retry > 0:
            try:
                if self.get_ip():
                    retry = retry - 1
                time.sleep(1)
            except:
                return
        raise Exception('wait_for_down timeout')

    @libvirt_wrapper
    def wait_for_destroy(self, retry=180):
        while retry > 0:
            try:
                self.vm.info()
                time.sleep(1)
                retry = retry - 1
            except:
                return
        raise Exception('wait_for_destroy timeout')

    def run(self, cmd, nohup=False, env=None):
        if nohup:
            cmd = 'nohup ' + cmd + ' > nohup.out 2>&1 &'
        if env:
            cmd = env + ' ' + cmd

        stdin, stdout, stderr = self.ssh_conn.exec_command(cmd)
        return stdout.read()

    def __get_files__(self, path):
        all_files = []
        all_subdirs = []
        if os.path.isdir(path):
            files = os.listdir(path)
            for x in files:
                filename = os.path.join(path, x)
                f, d = self.__get_files__(filename)
                all_files.extend(f)
                all_subdirs.extend(d)
            all_subdirs.append(path)
        elif os.path.isfile(path):
            all_files.append(path)

        return all_files, all_subdirs

    def upload(self, path_from, path_to):
        try:
            all_files, all_subdirs = self.__get_files__(path_from)
            # If there's sub dirs, the path_from mush be a dir
            # This operation will also create path_to if the dir doesn't exist.
            # Because the root dir is also replaced.
            for x in all_subdirs:
                dirname = x.replace(path_from, path_to)
                print dirname, path_to
                self.ssh_conn.exec_command('mkdir -p ' + dirname)

            sftp = self.ssh_conn.open_sftp()
            for x in all_files:
                remote_file = x.replace(path_from, path_to)
                sftp.put(x, remote_file)
            sftp.close()
        except:
            raise Exception(path_from, path_to)

    @libvirt_wrapper
    def create(self):
        try:
            self.vm = self.conn.createXML(self.xmlstr)
        except:
            raise Exception(self.xmlstr)

    @libvirt_wrapper
    def reboot(self):
        try:
            self.vm.reboot()
        except:
            raise Exception()

    @libvirt_wrapper
    def reset(self):
        try:
            self.vm.reset()
        except:
            raise Exception()

    @libvirt_wrapper
    def shutdown(self):
        try:
            self.vm.shutdown()
        except:
            raise Exception()

    @libvirt_wrapper
    def destroy(self):
        try:
            self.vm.destroy()
        except:
            raise Exception()
        finally:
            self.vm = None

    def load_module(self, param=''):
        try:
            self.run('modprobe amdgpu ' + param, nohup=True)
            time.sleep(3)
        except:
            raise Exception()

    def check_driver(self):
        stdout = self.run('lsmod |grep amdgpu')
        if 'amdgpu' not in stdout:
            raise Exception('No amdgpu loaded')

        stdout = self.run('dmesg')
        if 'Initialized amdgpu' not in stdout:
            raise Exception(stdout)

        stdout = self.run('cat /sys/kernel/debug/dri/0/amdgpu_fence_info')
        fence_info = stdout.split('\n')
        signaled = []
        emitted = []
        for line in fence_info:
            if 'signaled' in line:
                signaled.append(line.split(' ')[-1])
            elif 'emitted' in line:
                emitted.append(line.split(' ')[-1])
        for index in range(0, len(signaled)):
            if signaled[index] != emitted[index]:
                raise Exception(fence_info)

host = SriovHost()
