from django.urls import path
from .views import (HomeView, results, simulation, StreamView, GetSampleData, RunwayDataView, EndSimulationView,
                    CloseRunwayView, OpenRunwayView, ChangeTimescaleView, LiveResultsView)


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('results/', results, name='results'),
    path('simulation/',simulation, name='simulation'),
    path('stream/', StreamView.as_view(), name='stream'),
    path('api/sample-data/', GetSampleData.as_view(), name='sample-data'),
    path('api/runway-data/', RunwayDataView.as_view(), name='runway-data'),
    path('api/end-simulation/', EndSimulationView.as_view(), name='end-simulation'),
    path('api/close-runway/', CloseRunwayView.as_view(), name='close-runway'),
    path('api/open-runway/', OpenRunwayView.as_view(), name='open-runway'),
    path('api/change-timescale/', ChangeTimescaleView.as_view(), name='change-timescale'),
    path('api/live-results/', LiveResultsView.as_view(), name='live-results'),
]