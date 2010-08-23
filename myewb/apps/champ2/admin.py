from django.contrib import admin
from champ2 import models


class MatriceProgramAreaInline(admin.TabularInline):
    model = models.MatriceMetric
    extra = 8
class MatriceProgramAreaAdmin(admin.ModelAdmin):
    inlines = [
        MatriceProgramAreaInline,
    ]
    list_display = ('__unicode__', 'matrice_group','order','slug', 'title')
    list_filter = ('matrice_group','order','slug', 'title')
    list_editable = ('matrice_group','order','slug', 'title')


class MatriceMetricInline(admin.TabularInline):
    model = models.MatriceMetric
    extra = 10
class MatriceMetricAdmin(admin.ModelAdmin):
    inlines = [
        MatriceMetricInline,
    ]



#HELP??? http://docs.djangoproject.com/en/1.1/ref/contrib/admin/
admin.site.register(models.ProgramLink)
admin.site.register(models.ProgramArea)
admin.site.register(models.Goal)
admin.site.register(models.DateRange)
admin.site.register(models.ChampInfo)

admin.site.register(models.MatriceGroup)
admin.site.register(models.MatriceProgramArea, MatriceProgramAreaAdmin)
admin.site.register(models.MatriceMetric, MatriceMetricAdmin)
admin.site.register(models.MatriceDate)

admin.site.register(models.MatriceValueSet)
admin.site.register(models.MatriceMetricValue)
