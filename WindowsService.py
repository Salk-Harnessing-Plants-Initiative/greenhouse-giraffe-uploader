# Based on: https://gist.github.com/guillaumevincent/d8d94a0a44a7ec13def7f96bfb713d3f
import servicemanager
import socket
import sys
import win32event
import win32service
import win32serviceutil

import subprocess
PATH_TO_PYTHON = 'C:\\Users\\Greenhouse\\AppData\\Local\\Programs\\Python\\Python36\\python.exe'
PATH_TO_MAIN = "C:\\Users\\Greenhouse\\Documents\\greenhouse-giraffe-uploader\\main.py"

class TestService(win32serviceutil.ServiceFramework):
    _svc_name_ = "GiraffeUploaderService"
    _svc_display_name_ = "Giraffe Uploader Service"
    _svc_description_ = "Processes and uploads the images to AWS S3"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        rc = None
        with open('C:\\TestService.log', 'a') as f:
            f.write('hello world...\n')
            while rc != win32event.WAIT_OBJECT_0:
                f.write('apple...\n')
                try:
                    p = subprocess.run([PATH_TO_PYTHON, PATH_TO_MAIN], stdout=f, stderr=subprocess.STDOUT)
                except Exception as e:
                    f.write("ERROR: " + repr(e) + "\n")
                f.write('banana...\n')
                


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(TestService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(TestService)