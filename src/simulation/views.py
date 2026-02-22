from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .generation import Generator
from .serializers import SampleDataSerializer


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
    return render(request, 'pages/simulationtables.html')


class GetSampleData(APIView):
    serializer_class = SampleDataSerializer

    def get(self, request):
        generator = Generator(2, 15, 15)
        inbound, outbound = generator.run_generation()
        serializer = self.serializer_class(inbound + outbound, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)