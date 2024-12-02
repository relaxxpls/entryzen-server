"""gunicorn WSGI server configuration."""

from multiprocessing import cpu_count

bind = "unix:./gunicorn.sock"
workers = cpu_count() * 2 + 1
accesslog = "/var/log/gunicorn/entryzen/access.log"
errorlog = "/var/log/gunicorn/entryzen/error.log"

loglevel = "info"
capture_output = True

# max_requests = 1000
# worker_class = "gevent"
