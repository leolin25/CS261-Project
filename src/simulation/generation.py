from models import Aircraft

class Generator:
    def __init__(self, hour_limit, inbound_per_hour, outbound_per_hour):
        self.inbound_schedule = []
        self.outbound_schedule = []
        self.hour_limit = hour_limit
        self.inbound = inbound_per_hour
        self.outbound = outbound_per_hour
        self.last_generated = None

if __name__ == '__main__':
    pass