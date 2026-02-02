import random
from django.utils import timezone
from datetime import timedelta
from .models import Aircraft

airlines = [
    "BAW",  # British Airways
    "EZY",  # EasyJet
    "RYR",  # Ryanair
    "AFR",  # Air France
    "DLH",  # Lufthansa
    "UAE",  # Emirates
    "AAL",  # American Airlines
    "DAL",  # Delta
    "QFA",  # Qantas
    "SIA"   # Singapore Airlines
]

cities = ["LHR", "JFK", "CDG", "DXB", "LAX", "AMS", "FRA", "SIN", "HND"]

def generate_random_aircraft():
    