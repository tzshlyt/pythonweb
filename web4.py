#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import time
import os

SERVER_ADDRESS = (HOST, PORT) = '', 8888
REQUEST_QUEUE_SIZE = 5

def handle_request(client_conntction):
	request = client_conntction.recv(1024)

	print('Child PID: {pid}. Parent PID {ppid}'.format(pid=os.getpid(), ppid=os.getppid()))
	
	print(request.decode())

	http_response = b"""
HTTP/1.1 200 OK

Hello, World!
"""
	client_conntction.sendall(http_response)
	time.sleep(10)

def serve_forever():
	listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	listen_socket.bind(SERVER_ADDRESS)
	listen_socket.listen(REQUEST_QUEUE_SIZE)

	while True:
		client_conntction, client_address = listen_socket.accept()
		pid = os.fork()
		if pid == 0:
			listen_socket.close()
			handle_request(client_conntction)
			client_conntction.close()
			os._exit(0)
		else:
			client_conntction.close()


if __name__ == '__main__':
	print('Server: Serving HTTP on port {port} ...\n'.format(port=PORT))
	serve_forever()