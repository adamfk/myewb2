
from django import forms

from flexmodel.models import ObjectMultiSelectForm, DynamicSingleCheckboxForm
from champ2.models import ProgramArea, ChampInfo, ProgramLink, MatriceMetricValue, MatriceMetric

from django.template.defaultfilters import slugify
from django.core.exceptions import ObjectDoesNotExist




class ProgramAreaCheckBoxForm(DynamicSingleCheckboxForm):

    def __init__(self, request, *args, **kwargs):
        self.program_area = kwargs.pop('program_area')
        self.owner = kwargs.pop('owner')
        self.champ_info = kwargs.pop('champ_info') 
        self.field_label = kwargs.pop('field_label')  #this is the name used in the template for rendering the widget
        self._prefix = slugify(self.program_area.name)
        self._relative_post_name = "field"
        self._full_post_name = self._prefix + "-" + self._relative_post_name
        self._value = False      #read this value
        
        super(ProgramAreaCheckBoxForm, self).__init__(request, post_name=self._relative_post_name, field_name = self.field_label, css_class="prog_area_checkbox", prefix=self._prefix,*args, **kwargs) #call parent constructor

        #if no request data, fill it in ourselves
        if request == None:
            if ProgramLink.objects.filter(champ_info=self.champ_info, program_area=self.program_area).count() > 0:
                self._value = True
        else:
            #set value from request
            if self._full_post_name in request:
                self._value = True 

        self.fields[self._relative_post_name].initial = self._value


    def is_set(self):
        return self._value
        
#        if self.is_valid():
#            try:
#                print "ISSSSSSSSSSSSSSSSSSSSSSS SET:"
#                print repr(self.cleaned_data[self.post_name])
#                return self.cleaned_data[self.post_name]
#            except(KeyError):
#                pass
#            except(AttributeError):
#                pass
#
#        print "failed..."
#        return False

#===================================================================================================================================
# NOTE! there is some special code in here that figures out whether to pass request data to its parent constructor.
#          it will only pass request data if it can see data meant for this form (by checking names and the forms prefix).
#          If there is no data for this form, it does not pass the request data to the parent because then this form will be populated
#          with empty values incorrectly.

#note: instead of passing unamed 1st paramter result, now you have to name it like below
# form = MatriceProgramAreaForm(request=request, ...) 
class MatriceProgramAreaForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.matrice_value_set = kwargs.pop('matrice_value_set') #TODO: put in friendly raise error message
        self.matrice_program_area = kwargs.pop('matrice_program_area') #TODO: put in friendly raise error message
        self._prefix = "matrice" + str(self.matrice_value_set.id) + "_" + str(self.matrice_program_area.id)


        #try to get the request object that may have been passed in at start.
        request = None
        if kwargs.has_key("request"):
            request = kwargs.pop("request")
        if self._has_relevant_data(request) == False:
            request = None
            
   
        super(forms.Form, self).__init__(request, prefix=self._prefix,*args, **kwargs) #call parent constructor
              
        #get all MatriceMetrics for this MetricProgram area
        for metric in (self.matrice_program_area.metrics.all()):
            self.fields[metric.id] = forms.DecimalField(label=metric.title, max_digits=4, decimal_places=3, widget=forms.TextInput(attrs={'class':'matrice_input'}))   #TODO: remove magic numbers?
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
    
    #........................................        
    def _has_relevant_data(self, data=None):
        
        #if no passed in data (like the request), try the forms existing Data
        if data == None:
            try:
                data = self.data
            except(AttributeError):
                data = None
                
            if data == None:
                return False
        
        for metric in (self.matrice_program_area.metrics.all()):
            full_key = self._prefix + "-" + str(metric.id) #note: the "-" comes from Django's form name generation, not my code
            if data.has_key(full_key) == False:
                return False  #do not save if no data was in the form... otherwise it will just get wiped.
        
        return True
    
    def save(self):
        #Ensure that data was actually sent to this form by checking the POST data stored in self.data
        if self._has_relevant_data() == False:
            return False
        
     
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