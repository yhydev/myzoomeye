FROM python:3.6
RUN pip install requests 'requests[socks]' ratelimit pymongo redis celery "pymongo[srv]"