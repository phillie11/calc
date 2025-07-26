from django.shortcuts import render
from cars.models import Vehicle

def vehicle_list(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'cars/vehicle_list.html', {'vehicles': vehicles})