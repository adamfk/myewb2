
from django import forms
from flexmodel.models import ObjectMultiSelectForm, DynamicSingleCheckboxForm
from champ2.models import ProgramArea, ChampInfo, ProgramLink

from django.template.defaultfilters import slugify

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