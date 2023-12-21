class SyncSignal(object):
    def __init__(self, data=""):
        self.ip = ""
        self.port = 0
        self.data = data
        self.is_end = True


class HeartbeatSignal(SyncSignal):
    def __init__(self):
        super().__init__(data="Heartbeat")


class ConCheck(SyncSignal):
    def __init__(self):
        super().__init__(data="ConCheck")


class SyncData(SyncSignal):

    def __init__(self, data):
        super().__init__(data=data)
