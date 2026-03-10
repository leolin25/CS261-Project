import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse
from django.template import loader
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .generation import Generator
from .serializers import SampleDataSerializer
from .control import Controller
from .models import Aircraft, Runway, RunConfig


class HomeView(View):
    def get(self, request):
        return render(request, 'pages/home.html')

    # Need to add max wait
    # Need to remove runway status
    def post(self, request):
        valid = self.validate_input(request.POST)
        if not valid:
            return render(request, 'pages/home.html')
        runways = int(request.POST.get('num_runways'))
        operating_mode = request.POST.get('runway_mode')
        inbound = int(request.POST.get('inbound_flow'))
        outbound = int(request.POST.get('outbound_flow'))
        max_wait = 30
        if "random_events" in request.POST:
            random_events = True
        else:
            random_events = False
        RunConfig.objects.all().delete()
        RunConfig.objects.create(
            runways=runways,
            operating_mode=operating_mode,
            inbound_per_hour=inbound,
            outbound_per_hour=outbound,
            max_wait=max_wait,
            random_events=random_events,
        )
        return redirect('simulation')

    @staticmethod
    def validate_input(data):
        if "inbound_flow" not in data or "outbound_flow" not in data:
            return False
        if int(data["inbound_flow"]) < 0 or int(data["outbound_flow"]) < 0:
            return False
        if "num_runways" not in data:
            return False
        if int(data["num_runways"]) <= 0 or int(data["num_runways"]) > 10:
            return False
        if "runway_mode" not in data:
            return False
        if (data["runway_mode"].upper(), data["runway_mode"].capitalize()) not in Runway.MODE_CHOICES:
            print(6)
            return False
        return True


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
    num_runways = 7

    template = loader.get_template('pages/simulationtables.html')
    context = {
        'runway_range': range(1, num_runways + 1)

    }
    return HttpResponse(template.render(context, request))



class GetSampleData(APIView):
    serializer_class = SampleDataSerializer

    def get(self, request):
        generator = Generator(2, 15, 15)
        generator.run_generation()
        inbound = Aircraft.objects.filter(zone_status="SCHEDULED", scheduled_departure=None).order_by('queue_entry_time')
        outbound = Aircraft.objects.filter(zone_status="SCHEDULED", scheduled_arrival=None).order_by('queue_entry_time')
        serializer = self.serializer_class(list(inbound) + list(outbound), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


def stream(request):
    def event_stream():
        while True:
            controller.run_simulation()
            flight_data = controller.get_stream_data()
            serializer = SampleDataSerializer(flight_data, many=True)
            data = f"data: {json.dumps(serializer.data)}\n\n" 
            yield data

    controller = Controller(2, 10, 10, timescale=1, schedule_limit=2)
    controller.setup_simulation()
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response



