#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import dotenv
import os
import libserver

# Use .env file if it is found
env_path = os.getcwd() + '/.env'
if os.path.exists(env_path):
    dotenv.load_dotenv(env_path)

azure_host = os.environ.get('AZURE_HOSTNAME')
host = '0.0.0.0'
port_str = os.environ.get('WEBSITES_PORT')
port = int(port_str)

sel = selectors.DefaultSelector()

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    message = libserver.Message(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=message)

# host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Avoid bind() exception: OSError: [Errno 48] Address already in use
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((host, port))
lsock.listen()
print("listening on", (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                message = key.data
                try:
                    message.process_events(mask)
                except Exception:
                    print(
                        "main: error: exception for",
                        f"{message.addr}:\n{traceback.format_exc()}",
                    )
                    message.close()
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
