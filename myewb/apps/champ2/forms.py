
from django import forms

from flexmodel.models import ObjectMultiSelectForm, DynamicSingleCheckboxForm
from champ2.models import ProgramArea, ChampInfo, ProgramLink, MatriceMetricValue, MatriceMetric

from django.template.defaultfilters import slugify
from django.core.exceptions import ObjectDoesNotExist




class ProgramAreaCheckBoxForm(DynamicSingleCheckboxForm):

    def __init__(self, *args, **kwargs):
        self.program_area = kwargs.pop('program_area')
        self.owner = kwargs.pop('owner')
        self.champ_info = kwargs.pop('champ_info') 
        self.field_name = kwargs.pop('field_name')  #this is the name used in the template for rendering the widget
        self.prefix = slugify(self.program_area.name)
        
        
        #see if it is set
        initial = False
        if ProgramLink.objects.filter(champ_info=self.champ_info, program_area=self.program_area).count() > 0:
            initial = True
        
        prefix = self.prefix
        super(ProgramAreaCheckBoxForm, self).__init__(post_name=self.field_name, prefix=prefix,*args, **kwargs) #call parent constructor
        self.fields[self.field_name].initial = initial

    def is_set(self):
        self.is_valid()
            
        try:
            print repr(self.cleaned_data)
            return self.cleaned_data[self.field_name]      
        except(KeyError):
            pass
        return False


class MatriceProgramAreaForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.matrice_value_set = kwargs.pop('matrice_value_set') #TODO: put in friendly raise error message
        self.matrice_program_area = kwargs.pop('matrice_program_area') #TODO: put in friendly raise error message
        prefix = "matrice" + str(self.matrice_value_set.id) + "_" + str(self.matrice_program_area.id)
        
        super(forms.Form, self).__init__(prefix=prefix,*args, **kwargs) #call parent constructor
       
        #get all MatriceMetrics for this MetricProgram area
        for metric in (self.matrice_program_area.metrics.all()):
            self.fields[metric.id] = forms.DecimalField(label=metric.title, max_digits=4, decimal_places=3)   #TODO: remove magic numbers?
            self.fields[metric.id].required = False
            
            self.fields[metric.id].help1 = metric.help1 
            self.fields[metric.id].help2 = metric.help2
            self.fields[metric.id].help3 = metric.help3
            self.fields[metric.id].help4 = metric.help4
            
            #get value object for this metric
            try:
                self.fields[metric.id].initial = MatriceMetricValue.objects.get(matrice_metric = metric, matrice_value_set = self.matrice_value_set).value
            except(ObjectDoesNotExist):
                pass
            
            
    
    def save(self):
        #matrice_value_set
        #matrice_program_area
        
        for i, field_name in enumerate(self.fields):
            
            if field_name != "owner":
                metric_id = field_name
                matrice_metric = MatriceMetric.objects.get(matrice_program_area = self.matrice_program_area, id = metric_id)
            
                metric_value = None
                #try to find the metric value to update
                try:
                    metric_value = MatriceMetricValue.objects.get(matrice_metric = matrice_metric, matrice_value_set = self.matrice_value_set)
                except(ObjectDoesNotExist):
                    metric_value = MatriceMetricValue()
                    metric_value.matrice_metric = matrice_metric
                    metric_value.matrice_value_set = self.matrice_value_set
                
                
                self.is_valid() #force it to validate and fill cleaned_data[]
                metric_value.value = self.cleaned_data[field_name]
                metric_value.save()
            
    def clean(self):
        super(MatriceProgramAreaForm,self).clean()
        cleaned_data = self.cleaned_data
        
        for i, field_name in enumerate(self.fields):
            if field_name != "owner":
                if self.cleaned_data.has_key(field_name):
                    field_value = self.cleaned_data[field_name]
                    
                    if field_value:
                        if field_value < 1 or field_value > 4:
                            self._errors[field_name] = self.error_class(["Each value must be between 1 and 4."])
            
        # Always return the full collection of cleaned data.
        return self.cleaned_data
            
def getProgramAreasForm(champ_info, title, required, form_name):
    
    objects = ProgramArea.objects.all()
    #get all program areas for this champ_info
    
    has_program_areas = ProgramArea.objects.filter(ProgramLink__champ_info__id=champ_info.id)  #ChampInfo.objects.filter(id=champ_info.id, ProgramLink__program_area=1)

    #find the program areas that this is champ_info object is already associated with     
    initial = list()
    for i, pg in enumerate(has_program_areas):
        initial.append(pg.id)
        print pg.id

    return ObjectMultiSelectForm(objects=objects, title=title, required=required, form_name=form_name, initial=initial )
    pass