from sriov_test.core.domain import *
from sriov_test.core.case import *
import random
import time

def thread_func(data):
    case, capsys = data
    guest = case.container

    retries = 0
    while retries < 1000:
        ops = random.randint(1,1)
        if ops == 0:
            #destroy
            with capsys.disabled():
                print guest.get_name(),'destroy',retries, time.ctime()
            guest.destroy()
            guest.wait_for_destroy()
            guest.create()
            time.sleep(10)
            guest.wait_for_up()
        elif ops == 1:
            with capsys.disabled():
                print guest.get_name(),'reboot',retries, time.ctime()
            guest.reboot()
            guest.wait_for_down()
            guest.wait_for_up()
        elif ops == 2:
            with capsys.disabled():
                print guest.get_name(),'reset',retries, time.ctime()
            guest.reset()
            guest.wait_for_down()
            guest.wait_for_up()
        elif ops == 3:
            with capsys.disabled():
                print guest.get_name(),'shutdown',retries, time.ctime()
            guest.shutdown()
            guest.wait_for_destroy()
            guest.create()
            time.sleep(10)
            guest.wait_for_up()

        # if (retries % 2) == 0:
        guest.attach()
        guest.load_module()
        guest.check_driver()

        retries = retries + 1

def test_reboot(capsys):
    data = []
    guests = host.list_guests()
    for each in guests:
        each.load_module()
    tim = InstanceManager(guests)
    tim.attach_instances('dummy')

    tim.logics_map(thread_func, capsys)
    tim.logics_sync()
