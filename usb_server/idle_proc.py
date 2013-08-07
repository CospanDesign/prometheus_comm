
import sys
import signal
import socket

rsock, wsock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
rsock.setblocking(True)

rsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
wsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


def user1_event(signal_number, frame):
    print "Update\n"
    wsock.send('\0')

if __name__ == "__main__":
    signal.signal(signal.SIGUSR1, user1_event)
    print "Hello\n"
    while True:
        try:
            print "Wait for data from the write socket"
            rsock.recv(1)
            print "Read something"
        except socket.error, err:
            pass
        except KeyboardInterrupt, err:
            rsock.shutdown(socket.SHUT_RDWR)
            rsock.close()

            wsock.shutdown(socket.SHUT_RDWR)
            wsock.close()
            break

    print "Done!"

