#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import StringIO
import sys
import os
import time
import signal
import errno
import argparse
 
def grim_reaper(signum, frame):
    while True:
        try:
            pid, status = os.waitpid(
                -1,             # Wait for any child process
                os.WNOHANG      # Do not block and return EWOULDBLOCK error
            )
            print(
                'Child {pid} terminated with status {status}'
                '\n'.format(pid=pid, status=status)
            )
        except OSError:
            return
    
        if pid == 0:    # no more zombies
            return

class WSGIServer(object):
 
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1024
 
 	# 初始化 socket
    def __init__(self, server_address):
        # Create a listening socket
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )
        # Allow to reuse the same address
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind
        listen_socket.bind(server_address)
        # Activate
        listen_socket.listen(self.request_queue_size)
        # Get server host name and port
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # Return headers set by Web framework/Web application
        self.headers_set = []
 
    def set_app(self, application):
        self.application = application
 

 	# 死循环客户端的请求
    def serve_forever(self):
        listen_socket = self.listen_socket

        while True:
            # New client connection
            try:
                self.client_connection, client_address = listen_socket.accept()
            except IOError as e:
                code, msg = e.args
                if code == errno.EINTR:   # restart 'accept' if it was interrupted
                    continue
                else:
                    raise

            pid = os.fork()
            if pid == 0:
                listen_socket.close()
                # Handle one request and close the client connection. Then
                # loop over to wait for another client connection
                self.handle_one_request()
                os._exit(0)
            else:
                self.client_connection.close()
 

 	# 处理客户端的请求
    def handle_one_request(self):
        print('Child PID: {pid}. Parent PID {ppid}'.format(pid=os.getpid(), ppid=os.getppid()))
    	# 1、接收客户端请求
        self.request_data = request_data = self.client_connection.recv(1024)
        # Print formatted request data a la 'curl -v'
        print(''.join(
            '< {line}\n'.format(line=line)
            for line in request_data.splitlines()
        ))
 
 		# 2、处理请求(处理头部信息)
        self.parse_request(request_data)
 
 		# 3、使用请求数据构建环境信息
        # Construct environment dictionary using request data
        env = self.get_environ()
 
 		# 4、调用 app 处理并且返回响应结果
        # It's time to call our application callable and get
        # back a result that will become HTTP response body
        result = self.application(env, self.start_response)

 		# 5、构建响应体并返回客户端
        # Construct a response and send it back to the client
        self.finish_response(result)
 
    def parse_request(self, text):
        request_line = text.splitlines()[0]
        request_line = request_line.rstrip('\r\n')

        # Break down the request line into components
        (self.request_method,  # GET
         self.path,            # /hello
         self.request_version  # HTTP/1.1
         ) = request_line.split()

    def get_environ(self):
        env = {}
        # The following code snippet does not follow PEP8 conventions
        # but it's formatted the way it is for demonstration purposes
        # to emphasize the required variables and their values
        #
        # Required WSGI variables
        env['wsgi.version']      = (1, 0)
        env['wsgi.url_scheme']   = 'http'
        env['wsgi.input']        = StringIO.StringIO(self.request_data)
        env['wsgi.errors']       = sys.stderr
        env['wsgi.multithread']  = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once']     = False
        # Required CGI variables
        env['REQUEST_METHOD']    = self.request_method    # GET
        env['PATH_INFO']         = self.path              # /hello
        env['SERVER_NAME']       = self.server_name       # localhost
        env['SERVER_PORT']       = str(self.server_port)  # 8888
        return env
 
    # app 回调方法，传回 状态码 和 头部信息
    def start_response(self, status, response_headers, exc_info=None):
        # Add necessary server headers
        server_headers = [
            ('Date', 'Tue, 31 Mar 2015 12:54:48 GMT'),
            ('Server', 'WSGIServer 0.2'),
        ]
        self.headers_set = [status, response_headers + server_headers]
        # To adhere to WSGI specification the start_response must return
        # a 'write' callable. We simplicity's sake we'll ignore that detail
        # for now.
        # return self.finish_response
 
    def finish_response(self, result):
        try:
            status, response_headers = self.headers_set
            response = 'HTTP/1.1 {status}\r\n'.format(status=status)
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data
            # Print formatted response data a la 'curl -v'
            print(''.join(
                '> {line}\n'.format(line=line)
                for line in response.splitlines()
            ))

            # 发送到客户端
            self.client_connection.sendall(response)

            time.sleep(5)
        finally:
            self.client_connection.close()
            
 
 
SERVER_ADDRESS = (HOST, PORT) = '', 8888
 

def make_server(server_address, application):
    signal.signal(signal.SIGCHLD, grim_reaper)
    server = WSGIServer(server_address)
    server.set_app(application)
    return server
 
 
if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDRESS, application)
    print('WSGIServer: Serving HTTP on port {port} ...\n'.format(port=PORT))
    httpd.serve_forever()