from django.shortcuts import render, redirect, get_object_or_404
from .models import Aircraft, Runway
from .logic import generate_random_aircraft

def home(request):
    # Loads the home page with current simulation data
    return render(request, 'pages/home.html')

def results(request):
    #Loads results page
    return render(request, 'pages/results.html')

def simulation(request):
    #Loads simulation page
    return render(request, 'pages/simulationtables.html')
