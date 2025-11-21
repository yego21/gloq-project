from django.shortcuts import render


def medical(request):
    return render(request, "deep_dive/medical/medical.html")

