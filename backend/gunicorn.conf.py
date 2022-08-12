

bind = '0.0.0.0:8000'
wsgi_app = "arno.wsgi:application"
workers = 1
accesslog = '-'
loglevel = 'critical'
capture_output = True
enable_stdio_inheritance = True