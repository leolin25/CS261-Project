from django.urls import path
from .views import HomeView, results, simulation, stream, GetSampleData

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('results/', results, name='results'),
    path('simulation/',simulation, name='simulation'),
    path('api/sample-data/', GetSampleData.as_view(), name='sample-data'),
    path('stream/',stream, name='stream')


]