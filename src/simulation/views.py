import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse
from django.template import loader
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .generation import Generator
from .serializers import SampleDataSerializer, RunwaySerializer
from .control import Controller
from .models import Aircraft, Runway, RunConfig


class HomeView(View):
    def get(self, request):
        return render(request, 'pages/home.html')

    def post(self, request):
        valid = self.validate_input(request.POST)
        if not valid:
            return render(request, 'pages/home.html')
        runways_mixed = int(request.POST.get('num_runways_mixed'))
        runways_takeoff = int(request.POST.get('num_runways_to'))
        runways_landing = int(request.POST.get('num_runways_la'))
        runways = runways_mixed + runways_takeoff + runways_landing
        inbound = int(request.POST.get('inbound_flow'))
        outbound = int(request.POST.get('outbound_flow'))
        max_wait = int(request.POST.get('max_wait'))
        if "random_events" in request.POST:
            random_events = True
        else:
            random_events = False
        RunConfig.objects.all().delete()
        RunConfig.objects.create(
            runways=runways,
            runways_mixed=runways_mixed,
            runways_takeoff=runways_takeoff,
            runways_landing=runways_landing,
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
        if "num_runways_mixed" not in data or "num_runways_to" not in data or "num_runways_la" not in data:
            return False
        if int(data["num_runways_mixed"]) < 0 or int(data["num_runways_to"]) < 0 or int(data["num_runways_la"]) < 0:
            return False
        if int(data["num_runways_mixed"]) + int(data["num_runways_to"]) + int(data["num_runways_la"]) <= 0:
            return False
        if int(data["num_runways_mixed"]) + int(data["num_runways_to"]) + int(data["num_runways_la"]) > 10:
            return False
        if "max_wait" not in data:
            return False
        if int(data["max_wait"]) <= 0:
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


class StreamView(View):
    def get(self, request):
        def event_stream():
            controller = Controller()
            controller.setup_simulation()

            while not controller.check_simulation_end():
                controller.run_simulation()
                flight_data = controller.get_stream_data()
                controller.update_configuration()

                serializer = SampleDataSerializer(flight_data, many=True)
                payload = {
                    "time": controller.get_simulation_time().isoformat(),
                    "flights": serializer.data,
                }
                data = f"data: {json.dumps(payload)}\n\n"
                yield data

            yield "event: end\ndata: Simulation ended\n\n"

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class RunwayDataView(APIView):
    def get(self, request):
        runways = Runway.objects.all()
        serializer = RunwaySerializer(runways, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EndSimulationView(APIView):
    def get(self, request):
        config = RunConfig.objects.last()
        if not config:
            return Response(status=status.HTTP_404_NOT_FOUND)
        config.stop = True
        config.save()
        return Response({"message": "Simulation ended"}, status=status.HTTP_200_OK)


class CloseRunwayView(APIView):
    def post(self, request):
        runway_id = request.data.get("runway_id")
        try:
            runway_id = int(runway_id)
        except ValueError:
            return Response({"error": "Invalid runway ID"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            runway = Runway.objects.get(id=runway_id)
            runway.operational_status = 'RUNWAYINSPEC'
            runway.save()
            return Response({"message": f"Runway id {runway.id} bearing {runway.bearing} closed"}, status=status.HTTP_200_OK)
        except Runway.DoesNotExist:
            return Response({"error": "Runway not found"}, status=status.HTTP_404_NOT_FOUND)


class OpenRunwayView(APIView):
    def post(self, request):
        runway_id = request.data.get("runway_id")
        try:
            runway_id = int(runway_id)
        except ValueError:
            return Response({"error": "Invalid runway ID"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            runway = Runway.objects.get(id=runway_id)
            runway.operational_status = 'AVAILABLE'
            runway.save()
            return Response({"message": f"Runway id {runway.id} bearing {runway.bearing} opened"}, status=status.HTTP_200_OK)
        except Runway.DoesNotExist:
            return Response({"error": "Runway not found"}, status=status.HTTP_404_NOT_FOUND)


class ChangeTimescaleView(APIView):
    def post(self, request):
        timescale = request.data.get("timescale")
        try:
            timescale = float(timescale)
        except ValueError:
            return Response({"error": "Invalid timescale"}, status=status.HTTP_400_BAD_REQUEST)
        if timescale < 0.5 or timescale > 30:
            return Response({"error": "Timescale must be between 0.5 and 60"}, status=status.HTTP_400_BAD_REQUEST)
        config = RunConfig.objects.last()
        if not config:
            return Response({"error": "RunConfig not found"}, status=status.HTTP_404_NOT_FOUND)
        config.timescale = timescale
        config.save()
        return Response({"message": f"Timescale changed to {timescale}"}, status=status.HTTP_200_OK)
