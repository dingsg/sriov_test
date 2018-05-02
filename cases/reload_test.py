from sriov_test.core.domain import *
from sriov_test.core.case import *
from multiprocessing.pool import ThreadPool
import random
import time

def thread_func(data):
    case, capsys = data
    guest = case.container

    retries = 0
    while retries < 500:
        with capsys.disabled():
            print guest.get_name(),'reload',retries, time.ctime()
        guest.load_module()
        guest.check_driver()
        guest.run('rmmod amdgpu')
        retries = retries + 1

def test_reboot_with_3dmark(capsys):
    data = []
    guests = host.list_guests()

    for each in guests:
        each.load_module()
    tim = InstanceManager(guests)
    tim.attach_instances('dummy')

    tim.logics_map(thread_func, capsys)
    tim.logics_sync()
