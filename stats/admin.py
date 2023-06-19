from django.contrib import admin
from .models import ExperimentalResponse, ResponseEntry, CondensedPropertyKey, ParameterType, Parameter, Statistics

admin.site.register(ExperimentalResponse)
admin.site.register(ResponseEntry)
admin.site.register(CondensedPropertyKey)
admin.site.register(ParameterType)
admin.site.register(Parameter)
admin.site.register(Statistics)
