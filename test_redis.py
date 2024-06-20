import redis

try:
    r = redis.Redis(host='127.0.0.1', port=6379)
    r.ping()
    print("Connected to Redis!")
except redis.ConnectionError:
    print("Failed to connect to Redis.")
