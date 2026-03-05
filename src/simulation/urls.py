from django.urls import path
from .views import home, results, simulation, stream, liveviewtabular, GetSampleData

urlpatterns = [
    path('', home, name='home'),
    path('results/', results, name='results'),
    path('simulation/',simulation, name='simulation'),
    path('liveviewtabular/',liveviewtabular, name='liveviewtabular'),

    path('api/sample-data/', GetSampleData.as_view(), name='sample-data'),
    path('stream/',stream, name='stream')

]