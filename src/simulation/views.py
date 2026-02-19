from django.shortcuts import render, redirect, get_object_or_404
from .models import Aircraft, Runway
from .logic import generate_random_aircraft
from django.http import HttpResponse
from django.template import loader

def home(request):
    # Loads the home page with current simulation data
    return render(request, 'pages/home.html')

#def results(request):
    #Loads results page
    #return render(request, 'pages/results.html')

def results(request):
  template = loader.get_template('pages/results.html')
  context = {
    'inperhour': '15',
    'outperhour': '15',
    'numrunways': '10',
    'mixedorsingle': 'MIXED',
    'randomevents': 'OFF',

    'maxintakeoffQ': '10',
    'maxinlandingQ': '15',
    'maxinholding': '20',
    'averagehold': '10',
    'maxdelay': '60',
    'averagedelay': '10',
    'delayvariance': '3',
    'delayrange': '40',
    'numdiverted': '12',


  }
  return HttpResponse(template.render(context, request))

def simulation(request):
    #Loads simulation page
    return render(request, 'pages/simulationtables.html')
