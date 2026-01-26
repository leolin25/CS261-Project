from django.shortcuts import render

def home(request):
    # This simply loads the home.html file we just made
    return render(request, 'pages/home.html')