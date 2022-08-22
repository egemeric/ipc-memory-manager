import sys
from traceback import print_exc

import dbus


def main():
    bus = dbus.SystemBus()
    try:
        remote_object = bus.get_object("tr.gen.egemeric.dbus", "/DbusObject")
        hello_reply_list = remote_object.HelloWorld(
            "Hello from example-client.py!", dbus_interface="tr.gen.egemeric.HelloWorld")
    except dbus.DBusException:
        print_exc()
        sys.exit(1)

    print("client:", hello_reply_list)

    iface = dbus.Interface(remote_object, "tr.gen.egemeric.Interface")
    hello_reply_tuple = iface.GetTuple()

    print("client:", hello_reply_tuple)

    hello_reply_dict = iface.GetDict()

    print("client:", hello_reply_dict)

    signal_reply = iface.AppSignal()

    print("Signal Reply", signal_reply)

    try:
        pass
        # iface.RaiseException()
    except dbus.DBusException as e:
        print("client:", str(e))

    #print("client:", remote_object.Introspect(dbus_interface="org.freedesktop.DBus.Introspectable"))

    if sys.argv[1:] == ['--exit-service']:
        iface.Exit()


if __name__ == '__main__':
    main()
