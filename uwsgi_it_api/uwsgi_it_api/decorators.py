from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from functools import wraps
import base64

def need_certificate(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if request.META.has_key('HTTPS_DN'):
            return func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('Forbidden\n')
    return _decorator

def need_basicauth(func, realm='uwsgi.it api'):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        # first check for crossdomain
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Access-Control-Allow-Origin']  = '*'
            response['Access-Control-Allow-Methods']  = 'GET,POST,DELETE,OPTIONS'
            response['Access-Control-Allow-Headers']  = 'X-uwsgi-it-username,X-uwsgi-it-password'
            return response
        if request.META.has_key('HTTP_AUTHORIZATION'):
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2:
                if auth[0].lower() == "basic":
                    uname, passwd = base64.b64decode(auth[1]).split(':')
                    user = authenticate(username=uname, password=passwd)
                    if user and user.is_active:
                        login(request, user)
                        request.user = user
                        return func(request, *args, **kwargs)
        elif request.META.has_key('HTTP_X_UWSGI_IT_USERNAME') and request.META.has_key('HTTP_X_UWSGI_IT_PASSWORD'):
            uname = request.META['HTTP_X_UWSGI_IT_USERNAME'].decode('hex')
            passwd = request.META['HTTP_X_UWSGI_IT_PASSWORD'].decode('hex')
            user = authenticate(username=uname, password=passwd)
            if user and user.is_active:
                login(request, user)
                request.user = user
                response = func(request, *args, **kwargs)
                response['Access-Control-Allow-Origin']  = '*'
                return response

        response = HttpResponse('Unauthorized\n')
        response.status_code = 401
        response['Access-Control-Allow-Origin']  = '*'
        response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
        return response
    return _decorator
