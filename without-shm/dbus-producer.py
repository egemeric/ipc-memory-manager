from threading import Thread
from time import sleep
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


class DemoException(dbus.DBusException):
    _dbus_error_name = "tr.gen.egemeric.DbusException"


class DbusObject(dbus.service.Object):

    @dbus.service.method("tr.gen.egemeric.HelloWorld",
                         in_signature='s', out_signature='as')
    def HelloWorld(self, hello_message):
        print("service:", str(hello_message))
        return ["Hello", " from example-service.py", "with unique name"]

    @dbus.service.method("tr.gen.egemeric.RaiseException",
                         in_signature='', out_signature='')
    def RaiseException(self):
        raise DemoException('The RaiseException method does what you might '
                            'expect')

    @dbus.service.method("tr.gen.egemeric.Interface",
                         in_signature='', out_signature='(ss)')
    def GetTuple(self):
        return ("Hello Tuple", " from example-service.py")

    @dbus.service.method("tr.gen.egemeric.Interface",
                         in_signature='', out_signature='a{ss}')
    def GetDict(self):
        return {"first": "Hello Dict", "second": " from example-service.py"}
    
    @dbus.service.method("tr.gen.egemeric.Interface")
    def AppSignal(self):
        print("Signal Emitted")
        return 'Signal Emitted'

    @dbus.service.method("tr.gen.egemeric.Exit",
                         in_signature='', out_signature='')
    def Exit(self):
        DbusThread.mainloop.quit()


class DbusThread(Thread):
    mainloop = None
    service_bus = None

    def __init__(self):
        Thread.__init__(self)

    def run(self):
        DBusGMainLoop(set_as_default=True)

        DbusThread.service_bus = dbus.SystemBus()
        name = dbus.service.BusName(
            "tr.gen.egemeric.dbus", DbusThread.service_bus)
        object = DbusObject(DbusThread.service_bus, '/DbusObject')

        DbusThread.mainloop = GLib.MainLoop()
        print("Running example service.")
        DbusThread.mainloop.run()

    def join(self, timeout=3):
        DbusThread.mainloop.quit()
        return super().join(timeout)


if __name__ == '__main__':
    try:
        th = DbusThread()
        th.start()
        while(1):
            sleep(1)
    except KeyboardInterrupt:
        th.join()
