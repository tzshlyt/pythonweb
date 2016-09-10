#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket

HOST, PORT = '', 20080

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(1)
print 'waiting for connection...'

while True:
	client_connection, client_address = s.accept()
	request = client_connection.recv(1024)
	print request

	http_response = """
HTTP/1.1 200 OK

Hello, World!
"""

	client_connection.sendall(http_response)
	client_connection.close
