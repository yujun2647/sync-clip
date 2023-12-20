class SyncSignal(object):
    def __init__(self):
        self.ip = ""
        self.port = 0


class HeartbeatSignal(SyncSignal):
    pass


class ConCheck(SyncSignal):
    pass


class SyncData(SyncSignal):

    def __init__(self, data):
        super().__init__()
        self.data = data
