from django.urls import path
from .views import home, results, simulation, visualization, stream, GetSampleData

urlpatterns = [
    path('', home, name='home'),
    path('results/', results, name='results'),
    path('simulation/',simulation, name='simulation'),
    path('visualization/', visualization, name='visualization'),
    path('api/sample-data/', GetSampleData.as_view(), name='sample-data'),
    path('stream/',stream, name='stream')

]