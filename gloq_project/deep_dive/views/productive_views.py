from django.shortcuts import render


def productive(request):
    return render(request, "deep_dive/productive/productive.html")

