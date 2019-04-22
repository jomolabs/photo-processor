import urllib.request

class FetchService(object):
    def __init__(self):
        pass

    def download(self, url, dst):
        urllib.request.urlretrieve(url, dst)
