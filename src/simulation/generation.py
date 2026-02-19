from models import Aircraft
from numpy import random

class Generator:
    def __init__(self, hour_limit, inbound_per_hour, outbound_per_hour):
        self.inbound_schedule = []
        self.outbound_schedule = []
        self.hour_limit = hour_limit
        self.inbound = inbound_per_hour
        self.outbound = outbound_per_hour
        self.last_generated = None

    @staticmethod
    def generate_sample():
        # Average delay of 0 minutes with a standard deviation of 5 minutes
        return int(round(random.normal(loc=0, scale=5)))


if __name__ == '__main__':
    pass