from django.shortcuts import render


def creative(request):
    return render(request, "deep_dive/creative/creative.html")

