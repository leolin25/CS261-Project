from django.urls import path
from .views import home, results, sim, GetSampleData

urlpatterns = [
    path('', home, name='home'),
    path('results/', results, name='results'),
    path('simulation/',sim.simulation, name='simulation'),
    path('api/sample-data/', GetSampleData.as_view(), name='sample-data'),
    path('stream/',sim.stream, name='stream'),
    path('getRunwaysSim/',sim.getRunwaysSim, name='getRunwaysSim')

]