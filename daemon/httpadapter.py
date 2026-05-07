#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.

    The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
    dispatching them to appropriate route handlers, and constructing responses.
    It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
    and :class:`Response <Response>` objects for full request lifecycle management.

    Attributes:
        ip (str): IP address of the client.
        port (int): Port number of the client.
        conn (socket): Active socket connection.
        connaddr (tuple): Address of the connected client.
        routes (dict): Mapping of route paths to handler functions.
        request (Request): Request object for parsing incoming data.
        response (Response): Response object for building and sending replies.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.

        :param ip (str): IP address of the client.
        :param port (int): Port number of the client.
        :param conn (socket): Active socket connection.
        :param connaddr (tuple): Address of the connected client.
        :param routes (dict): Mapping of route paths to handler functions.
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        """
        Handle an incoming client connection.

        This method reads the request from the socket, prepares the request object,
        invokes the appropriate route handler if available, builds the response,
        and sends it back to the client.

        :param conn (socket): The client socket connection.
        :param addr (tuple): The client's address.
        :param routes (dict): The route mapping for dispatching requests.
        """
        print("Client connected from", addr)
        # Connection handler.
        self.conn = conn        
        # Connection address.
        self.connaddr = addr
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        # Handle the request
        msg = conn.recv(1024).decode()
        req.prepare(msg, routes)

        #get req body
        body=req.body
        
        # Flag to track if this request just authenticated
        just_authenticated = False

        #TASK 1A: Implement authentication handling
        if req.method == "POST" and req.path == "/login":
            import urllib.parse
            params = {}
            for pair in body.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    # URL decode the values
                    params[urllib.parse.unquote_plus(key)] = urllib.parse.unquote_plus(value)
            
            print("[Auth] Login attempt with params:", params)
            
            if params.get("username") == "admin" and params.get("password") == "password":
                print("[Auth] Login successful!")
                #auth_result = True
                req.prepare_auth(True)
                req.path = '/index.html'
                just_authenticated = True

                # Set cookie properly in resp.cookies (not headers)
                resp.cookies['auth'] = 'true'
                resp.status_code=200
                resp.reason='OK'
            else:
                print("[Auth] Login failed - invalid credentials")
                print("[Auth] Expected: username=admin, password=password")
                print("[Auth] Got: username={}, password={}".format(params.get("username"), params.get("password")))
                conn.sendall(resp.build_unauthorized())
                conn.close()
                return #401
        #TASK 1B: Implement cookie-based authentication
        protected_paths = ["/","/login", "/index.html"]

        if not just_authenticated and req.method == "GET" and req.path in protected_paths:
            auth = req.cookies.get("auth")
            if not auth:
                # user is NOT authenticated 
                # Always redirect to login.html instead of returning 401
                req.path = "/login.html"
            else:         
                req.path = "/index.html"  

        #TASK 2.1: Handle the auth for the API
        protected_tracker_API = ["/submit-info","/add-list", "/remove"]

        if req.path in protected_tracker_API:
            # print("req.path",req.path)
            auth = req.cookies.get("auth")
            
            # print("req.cookies",req.cookies)
            # print("auth",auth)
            if not auth:
                # user is NOT authenticated 
                req.hook = None
                if req.path == "/login":
                    req.path = "/login.html"
                else:
                    # print("3333333333333333")
                    conn.sendall(resp.build_unauthorized())
                    conn.close()
                    return
            # print("4444444444444444")
        # Handle request hook
        if req.hook:
            print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path,req.hook._route_methods)) # o day bi nguoc ha ta?

            #req.hook(headers = "bksysnet",body = "get in touch")
            headers = ""
            body = ""
            if "\r\n\r\n" in msg:
                msg = msg.split("\r\n\r\n")
                headers = msg[0]
                body = msg[1]
            else:
                headers = msg
            print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path,req.hook._route_methods))
            status_code, hook_body = req.hook(headers = headers,body = body)
            resp.status_code = status_code
            #
            # TODO: handle for App hook here
            #
            reason_map = {
                200: "OK",
                201: "Created",
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                500: "Internal Server Error",
            }
            resp.reason = reason_map.get(status_code, "OK")

            # For hook payloads other than "OK", respond directly as API JSON.
            # This avoids relying on shared return.json across multiple processes.
            if hook_body != "OK":
                hook_body = self._normalize_hook_body_for_json(hook_body)
                response = resp.build_api_response(status_code, hook_body)
                conn.sendall(response)
                conn.close()
                return

        
        # Build response
        response = resp.build_response(req)


        #print(response)
        conn.sendall(response)
        conn.close()
    
    @property
    def extract_cookies(self, req, resp):
        """
        Retrieve cookies that are already parsed by the Request object.
        """
        # Since Request.prepare() already did the work, just return that.
        if req.cookies:
            return req.cookies
        return {}

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object 

        :param req: The :class:`Request <Request>` used to generate the response.
        :param resp: The  response object.
        :rtype: Response
        """
        response = Response()

        # Set encoding.
        response.encoding = 'utf-8'#get_encoding_from_headers(response.headers)
        response.raw = resp
        response.reason = response.raw.reason

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        # Add new cookies from the server.
        response.cookies = self.extract_cookies(req,resp)

        # Give the Response some context.
        response.request = req
        response.connection = self

        return response

    # def get_connection(self, url, proxies=None):
        # """Returns a url connection for the given URL. 

        # :param url: The URL to connect to.
        # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
        # :rtype: int
        # """

        # proxy = select_proxy(url, proxies)

        # if proxy:
            # proxy = prepend_scheme_if_needed(proxy, "http")
            # proxy_url = parse_url(proxy)
            # if not proxy_url.host:
                # raise InvalidProxyURL(
                    # "Please check proxy URL. It is malformed "
                    # "and could be missing the host."
                # )
            # proxy_manager = self.proxy_manager_for(proxy)
            # conn = proxy_manager.connection_from_url(url)
        # else:
            # # Only scheme should be lower case
            # parsed = urlparse(url)
            # url = parsed.geturl()
            # conn = self.poolmanager.connection_from_url(url)

        # return conn


    def add_headers(self, request):
        """
        Add headers to the request.

        This method is intended to be overridden by subclasses to inject
        custom headers. It does nothing by default.

        
        :param request: :class:`Request <Request>` to add headers to.
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 

        :class:`HttpAdapter <HttpAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        username, password = ("user1", "password")

        if username:
            headers["Proxy-Authorization"] = (username, password)

        return headers

    def _normalize_hook_body_for_json(self, hook_body):
        """
        Convert hook output to JSON-safe text without extra imports.
        """
        if hook_body is None:
            return "\"\""

        text = str(hook_body).strip()
        if text == "":
            return "\"\""

        # Already JSON object/array/string/primitive -> keep as-is
        if (
            text.startswith("{") or
            text.startswith("[") or
            (text.startswith("\"") and text.endswith("\"")) or
            text in ("true", "false", "null")
        ):
            return text

        # numeric primitive
        is_number = True
        dot_count = 0
        for idx, ch in enumerate(text):
            if ch == "-" and idx == 0:
                continue
            if ch == ".":
                dot_count += 1
                if dot_count > 1:
                    is_number = False
                    break
                continue
            if not ch.isdigit():
                is_number = False
                break
        if is_number:
            return text

        # fallback: encode as JSON string
        escaped = text.replace("\\", "\\\\").replace("\"", "\\\"")
        return "\"" + escaped + "\""

