from sriov_test.core.domain import *

def test_reboot_domain():
    guests = host.list_guests()
    for each in guests:
        each.reboot()

    for each in guests:
        each.wait_for_down(3000)

    for each in guests:
        each.wait_for_up(3000)
        each.upload('config.py', '/tmp/')
