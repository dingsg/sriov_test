from sriov_test.core.domain import *
from sriov_test.core.case import *

def test_glxgears():
    guests = host.list_guests()
    for each in guests:
        each.check_driver()
    # cm = CaseManager(guests)
    # cm.attach('glxgears')
    # cm.attach('3dmark', 2)
    # cm.run()
    # cm.finish()
    # cases = cm.list_cases()
    # for each in cases:
    #     if each.name == '3dmark':
    #         print each.analysis()
    # cm.detach()
