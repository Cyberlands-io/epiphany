class Page:

    first_load_time = 0
    second_load_time = 0
    cache_control = ''
    expires = ''
    etag = ''
    last_modified = ''
    payload = {}

    def __init__(self, url = "", method = "get"):
        
        self.url = url
        self.method = method
        if not self.method:
            self.method = 'get'
