import time
from pprint import pprint

import requests

NUM_REQUESTS = 20000
WAIT_TIME = 1
start = time.time()
errors = 0

try:
    with requests.session() as s:
        for i in range(1, NUM_REQUESTS+1):
            res = s.post("http://localhost:8080/v1/inference", json={"text": "lorem ipsum", "services": ["Service1:v1.0.0", "Service2:v1.0.0"]})
            if res.status_code != 200:
                errors += 1
            if __debug__:
                pprint(res.json())
                time.sleep(WAIT_TIME)
except KeyboardInterrupt:
    pass

diff = time.time() - start
print(f"{i} requests took {diff} or {diff / i} per request, errors {errors}")
