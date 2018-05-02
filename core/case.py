from sriov_test.utils.utils import *
from multiprocessing.pool import ThreadPool
import time
import case

class GuestApp(object):
    def __init__(self, container, name):
        self.name = name
        self.container = container
        self.runner = container.run
        self.uploader = container.upload
        self.source_path = abs_path(__file__) + '/apps/' + name
        self.target_path = '/tmp/' + name

    def attach(self):
        self.uploader(self.source_path, self.target_path)
        self.runner('chmod a+x '+ self.target_path + '/*')

    def is_installed(self):
        return True

    # async method, return immediately
    def install(self):
        return self.runner(self.target_path + '/install.sh', nohup=True)

    def setup(self):
        return self.runner(self.target_path + '/setup.sh')

    def launch_async(self, param=''):
        return self.runner(self.target_path + '/launch.sh ' + param, nohup=True)

    def launch_sync(self, param=''):
        return self.runner(self.target_path + '/launch.sh ' + param)

    def get_result(self):
        self.result = self.runner(self.target_path + '/result.sh')
        return self.result

    def is_finished(self):
        return True

    def force_finish(self):
        pass

    def cleanup(self):
        return self.runner(self.target_path + '/cleanup.sh')

    def analysis_result(self):
        pass

    def __is_running__(self, process):
        stdout = self.runner('ps -e |grep ' + process)
        if process in stdout:
            return True
        else:
            return False

# you can use dummy if there's no actual tests running in guest
class dummy(GuestApp):
    def __init__(self, container):
        super(dummy, self).__init__(container, 'dummy')

    def attach(self):
        pass

    def is_installed(self):
        return True

    def install(self):
        return True

    def setup(self):
        return True

    def launch_async(self):
        return True

    def launch_sync(self):
        return True

    def get_result(self):
        return True

    def is_finished(self):
        return True

    def force_finish(self):
        pass

    def cleanup(self):
        return True

    def analysis_result(self):
        pass

    def __is_running__(self, process):
        return False

class glxgears(GuestApp):
    def __init__(self, container):
        super(glxgears, self).__init__(container, 'glxgears')

    def is_finished(self):
        return self.__is_running__('glxgears')

class InstanceManager(object):
    def __init__(self, containers):
        self.containers = containers
        self.test_instances = []
        self.pool = ThreadPool(20) #20 threads so far
        pass

    # get the class obj from class name
    def __get_class__(self, case_name):
        return eval('case.'+case_name)

    # Return code: True is done, False is timed out
    def __wait_for_instances_method__(self, method_name, timeout=3600):
        while timeout > 0:
            all_done = True
            for each in self.test_instances:
                is_done = eval('each.'+method_name)
                all_done = all_done & is_done()
            if all_done == True:
                return True
            time.sleep(5)
            timeout = timeout - 5

        return False

    def __iter_instances_method__(self, method_name):
        for each in self.test_instances:
            func = eval('each.'+method_name)
            try:
                func()
            except:
                raise Exception('Invalid method %s' % method_name)

    def attach_instances(self, case_name, count=None):
        if count == None or count > len(self.containers):
            count = len(self.containers)
        for index in range(0, count):
            cls = self.__get_class__(case_name)
            case = cls(self.containers[index])
            case.attach()
            self.test_instances.append(case)
        return self.test_instances

    def install_app(self, timeout=3600):
        for each in self.test_instances:
            if each.is_installed() is False:
                each.install()

        return self.__wait_for_instances_method__('is_installed')

    def detach_instances(self):
        self.test_instances = []

    def list_instances(self):
        return self.test_instances

    # The simple_* methods are legacy to support simple tests
    # which just need to run in guests without complex logics.
    # For complex logics, please use logics_*.
    def simple_launch_tests(self):
        self.__iter_instances_method__('setup')
        time.sleep(2)
        self.__iter_instances_method__('launch_async')
        time.sleep(2)

    def simple_collect_results(self):
        self.__iter_instances_method__('get_result')

    def simple_cleanup_tests(self):
        self.__iter_instances_method__('cleanup')

    def simple_wait_for_tests_done(self, timeout=3600):
        return self.__wait_for_instances_method__('is_finished')

    # The func_for_each_vm will be applied on each VM in a thread.
    # It recieves parameter (case, capsys) and can get all stuffs
    # from case instance.
    # only async launching 
    def logics_map(self, func_for_each_vm, capsys=None):
        data = []
        for each in self.test_instances:
            data.append((each, capsys))
        self.pool_result = self.pool.map_async(func_for_each_vm, data)

    def logics_sync(self):
        try:
            while True:
                self.pool_result.wait(1)
                if self.pool_result.ready() is True:
                    E = self.pool_result.get()
                    for each in E:
                        assert each is None, each
                    break

            self.pool.close()
            self.pool.join()
        except KeyboardInterrupt:
            pass
        
if __name__ == "__main__":
    pass
