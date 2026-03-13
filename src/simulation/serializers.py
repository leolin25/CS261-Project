from rest_framework import serializers
from .models import Aircraft, Runway

class AircraftSerializer(serializers.ModelSerializer):
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
            'assigned_runway',
            'fuel_mins',
            'emergency_status',
            'zone_status',
            'last_update',
            'final_state_time',
        )


class RunwaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Runway
        fields = (
            'id',
            'length',
            'bearing',
            'operating_mode',
            'occupied_by',
            'time_occupied',
            'operational_status',
            'temp_optimised',
        )