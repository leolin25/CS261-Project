from rest_framework import serializers
from .models import Aircraft

class SampleDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aircraft
        fields = (
            'callsign',
            'operator',
            'origin',
            'destination',
            'scheduled_arrival',
            'scheduled_departure',
            'queue_entry_time',
            'altitude',
            'fuel_mins',
            'emergency_status',
            'zone_status'
        )