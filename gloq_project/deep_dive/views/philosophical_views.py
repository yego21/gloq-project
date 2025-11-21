from django.shortcuts import render


def philosophical(request):
    return render(request, "deep_dive/philosophical/philosophical.html")

