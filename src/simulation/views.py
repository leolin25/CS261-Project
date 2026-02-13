from django.shortcuts import render, redirect, get_object_or_404
from .models import Aircraft, Runway
from .logic import generate_random_aircraft

def home(request):
    # Loads the home page with current simulation data
    return render(request, 'pages/home.html')
