from django.contrib import admin
from flexmodel import models

#HELP??? http://docs.djangoproject.com/en/1.1/ref/contrib/admin/

class AnyFieldAdmin(admin.ModelAdmin):
    list_display = ('name','pk','field_group', 'type', 'order', 'private', 'visible', 'required', 'parent_field')
    list_filter = ('field_group','private','type', 'visible','required' ,'parent_field')
    list_editable = ('field_group','order', 'type', 'private', 'visible','required', 'parent_field')
    save_as = True


class AnyFieldInline(admin.TabularInline):
    model = models.AnyField
    extra = 10

class FieldGroupAdmin(admin.ModelAdmin):
    inlines = [
        AnyFieldInline,
    ]

class AnyValueInline(admin.TabularInline):
    model = models.AnyValue
    extra = 5

class AnyValueOwnerAdmin(admin.ModelAdmin):
    inlines = [
        AnyValueInline,
    ]

admin.site.register(models.FieldGroup, FieldGroupAdmin)
admin.site.register(models.AnyField, AnyFieldAdmin)
admin.site.register(models.AnyValue)
admin.site.register(models.Calc)
admin.site.register(models.AnyValueOwner, AnyValueOwnerAdmin)

