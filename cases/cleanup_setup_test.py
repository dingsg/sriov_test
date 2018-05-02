from sriov_test.core.helper import *

def test_cleanup():
    unload_gim()
    remove_test_images()
    run('rm -rf ~/.ssh/known_hosts')

def test_setup():
    create_test_images()
    load_gim()
