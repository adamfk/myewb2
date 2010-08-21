from django.contrib import admin
from champ2 import models

#HELP??? http://docs.djangoproject.com/en/1.1/ref/contrib/admin/
admin.site.register(models.ProgramLink)
admin.site.register(models.ProgramArea)
admin.site.register(models.Goal)
admin.site.register(models.DateRange)
admin.site.register(models.ChampInfo)

admin.site.register(models.MatriceGroup)
admin.site.register(models.MatriceProgramArea)
admin.site.register(models.MatriceMetric)
admin.site.register(models.MatriceDate)
admin.site.register(models.MatriceValueSet)
admin.site.register(models.MatriceMetricValue)
