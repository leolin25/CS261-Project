from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.test import Client
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .generation import Generator
from .serializers import SampleDataSerializer
import datetime
import time
from django.http import StreamingHttpResponse
import json

def home(request):
    # Loads the home page with current simulation data
    return render(request, 'pages/home.html')


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
    #takeoffQ = Member.objects.all().values()
    #landingQ = Member.objects.all().values()

    template = loader.get_template('pages/simulationtables.html')
    context = {
       #'takeoffQ': takeoffQ,
       #'landingQ': landingQ,
    }
    return HttpResponse(template.render(context, request))


class GetSampleData(APIView):
    serializer_class = SampleDataSerializer

    def get(self, request):
        generator = Generator(2, 15, 15)
        inbound, outbound = generator.run_generation()
        serializer = self.serializer_class(inbound + outbound, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def getinternal(self):
        generator = Generator(2, 15, 15)
        inbound, outbound = generator.run_generation()
        serializer = self.serializer_class(inbound + outbound, many=True)
        return serializer.data


#Stream test using date time
def stream(request):
    def event_stream():
        while True:
            time.sleep(1)
            provider = GetSampleData()
            takeoffQ = provider.getinternal()
            #yield 'data: The server time is: %s\n\n' % datetime.datetime.now()
            data = f"data: {json.dumps(takeoffQ)}\n\n" #neeed to define takeoffQ, should just be a json file 
            yield data
    
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

