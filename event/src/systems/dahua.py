import requests

def get_snapshot(location, endpoint, auth):
    r = requests.get(endpoint, auth=auth)
    logger.debug(r)

    with open(fn := f'{location}-{datetime.datetime.now()}.jpg', 'wb') as f:
        f.write(r.content)

    return fn