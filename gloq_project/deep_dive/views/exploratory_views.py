from django.shortcuts import render


def exploratory(request):
    return render(request, "deep_dive/exploratory/exploratory.html")

