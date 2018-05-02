import os
import re

# methods
def run(cmd):
    try:
        r = os.popen(cmd)
    except:
        print("Invalid cmd:" + cmd)

    return r.read()

def abs_path(curr):
    return os.path.dirname(os.path.abspath(curr))

def ssh_setup(account, password, ip):
    cmd = abs_path(__file__)+'/auto_ssh.sh %s %s %s %s' % (account, password, ip, os.environ['HOME'])
    run(cmd)

def list_vfs(did):
    res = []
    cmd = "lspci |grep " + did + "|awk {'print $1'}"
    vfs = run(cmd).split('\n')
    for vf in vfs:
        bdf = re.split('[:.]',vf)
        if len(bdf) == 3:
            entry = {}
            entry['bus'] = bdf[0]
            entry['device'] = bdf[1]
            entry['function'] = bdf[2]
            res.append(entry)
    return res
