from django.db import models
from django.forms import ModelForm  #used for creating forms at bottom of page

from django.db.models import forms
#from champs.dprint import dumpObj  #for fancy debug printing

from settings import DEBUG

from django.db.models.aggregates import Sum

from EquationParser import parse_equation, ParseCommand, ParseNumber, ParseOperation
from django.db.models.aggregates import Sum
from django.core.exceptions import ObjectDoesNotExist

from django.db.models.base import Empty

#NOTE: the coupled import. not great, but needed now.


#class MyException(Exception):
#    def _get_message(self): 
#        return self._message
#    def _set_message(self, message): 
#        self._message = message
#    message = property(_get_message, _set_message)

class CustomException(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

# MANAGER
class FieldGroupManager(models.Manager):
    def get_visible_fields(self, field_group, get_children=False):
        q = field_group.anyfield_set.filter(visible=1).order_by('order')
        if get_children == False:
            q = q.filter(parent_field=None)
            #dumpObj(q.all())
        return q

class FieldGroup(models.Model):
    
    name = models.CharField(max_length = 50)
    slug = models.CharField(max_length = 10, unique = True)
    objects = FieldGroupManager()
    
    def __unicode__(self):
        return self.name


#Used to create a multi selectable form from objects passed to it
"""
objects should be triple of: object id, title, initial value
"""
class ObjectMultiSelectForm(forms.Form):
    
    #====================================
    # ------------ constructor ----------
    #====================================
    def __init__(self, *args, **kwargs):
  
        objects = kwargs.pop('objects')
        title = kwargs.pop('title')
        required = kwargs.pop('required')
        form_name = kwargs.pop('form_name')
        initial = kwargs.pop('initial')

        super(forms.Form, self).__init__(*args, **kwargs) #call parent constructor

        choices = list()
        
        for i, obj in enumerate(objects):
            choices.append((obj.id, obj.name) ) #TODO: best to not hardcode .name
            
        self.fields[form_name] = forms.MultipleChoiceField(choices=choices, label=title, widget=forms.CheckboxSelectMultiple)
        
        if initial:
            self.fields[form_name].initial = initial
        
        if required:
            self.fields[form_name].required = True  


class DynamicSingleCheckboxForm(forms.Form):

    def __init__(self, *args, **kwargs):
  
        prefix = kwargs.pop('prefix')
        post_name = kwargs.pop('post_name')
        
        super(DynamicSingleCheckboxForm, self).__init__(prefix=prefix,*args, **kwargs) #call parent constructor
        self.fields[post_name] = forms.BooleanField( widget=forms.widgets.CheckboxInput(attrs={'class':'special_class'}))
        self.fields[post_name].required = False
        

#
#class GroupWidget(forms.HiddenInput):
#    
#   
#    def set_child_form(self, form):
#        self.child_form = form
#    
#    def render(self, name, value, attrs=None):
#        
#        result =  "<fieldset><legend>" + str(self.legend) + "</legend>"
#    
#        result = result + self.child_form.as_p()
#        
#        result = result + "</fieldset>"
#        
#        print result
#        return result


class FieldsetStartWidget(forms.Widget):
    
    def __init__(self, *args, **kwargs):
        self.legend = "something"
        if 'legend' in kwargs:
            self.legend = kwargs.pop('legend')
        super(FieldsetStartWidget, self).__init__() #call parent constructor
        
    def render(self, name, value, attrs=None):
        #result =  "<fieldset><legend>" + str(self.legend) + "</legend>"
        result = "<div>"
        return result


class FieldsetEndWidget(forms.Widget):

    def render(self, name, value, attrs=None):
        
        result =  "</fieldset>"
        result =  "</div>"
        return result

                
#====================================#====================================
# 
#====================================#====================================
class FieldGroupForm(forms.Form):
    
    #if calc_mode = 'form', then it does not compile calculations,
    #if calc_mode = 'calc_plan', then it calculates for plans
    #if calc_mode = 'calc_eval', then it calculates for evaluations 
    CALC_MODE_FORM = "form"
    CALC_MODE_PLAN = "plan"
    CALC_MODE_EVAL = "eval"    
    
    #====================================
    # ------------ constructor ----------
    #====================================
    def __init__(self, *args, **kwargs):
  
        field_group = kwargs.pop('field_group')
        owner = kwargs.pop('owner')
        assert field_group
        
        #pull off optional parameters
        calc_base_group = None #by default unless passed in
        if 'calc_base_group' in kwargs:
            calc_base_group = kwargs.pop('calc_base_group')
            
        calc_mode = self.CALC_MODE_FORM  
        if 'calc_mode' in kwargs:
            calc_mode = kwargs.pop('calc_mode')

        calc_parent_class = None  
        if 'calc_parent_class' in kwargs:
            calc_parent_class = kwargs.pop('calc_parent_class')
        
        extra_prefix = ""
        if 'extra_prefix' in kwargs:
            extra_prefix = kwargs.pop('extra_prefix')
        
        self._form_prefix = field_group.slug + extra_prefix
       
        super(forms.Form, self).__init__(prefix = self._form_prefix,*args, **kwargs) #call parent constructor
        self.fields["owner"] = forms.IntegerField(initial=owner.id, widget=forms.widgets.HiddenInput())
        
        #get all fields for this field group
        fields = FieldGroup.objects.get_visible_fields(field_group, get_children=False)
        for i, field in enumerate(fields):
            self.initialize_field(self, field, owner, calc_base_group, calc_mode, calc_parent_class)
    
    @classmethod
    #cls = this class object autopassed in by python
    def initialize_field(cls, form, field, owner, calc_base_group, calc_mode, calc_parent_class):
        form.fields[cls.get_post_name(field)] = cls.field_2_formfield(field)
        form.fields[cls.get_post_name(field)].required = False #field.required
        form.fields[cls.get_post_name(field)].is_group = False #by default... changed if actually a group
             
        #=========================================================
        if field.type == AnyField.SINGLE_CHOICE_TYPE:
            #try to find initial value for it
            print "Single choice value starting " + field.title
            kid_fields = AnyField.objects.get_children(field)
            
            #find the one that is set
            for kid_field in kid_fields:
                kid_values = AnyValue.objects.filter_by(owner=owner, any_field=kid_field).filter(integer=1)
                if kid_values.count() > 0:
                    form.fields[cls.get_post_name(field)].initial = kid_field.id


        #=========================================================
        elif field.type == AnyField.MULTIPLE_CHOICE_TYPE:
            #try to find initial value for it
            print "multi choice value starting " + field.title
            kid_fields = AnyField.objects.get_children(field).filter(anyvalue__integer=1)      
           
            #find the ones that are set
            initial = list()
            for kid_field in kid_fields:
                initial.append(kid_field.id)

            form.fields[cls.get_post_name(field)].initial = initial

        #-----------------GROUP TYPE--------------------------------
        elif field.type == AnyField.GROUP_TYPE:
            print "GRRRROUP starting " + field.title
            kid_fields = AnyField.objects.get_children(field)      

            for kid_field in kid_fields:
                cls.initialize_field(form, kid_field, owner, calc_base_group, calc_mode, calc_parent_class)
            
            form.fields[cls.get_post_name(field) + "groupend"] = forms.CharField(widget=FieldsetEndWidget())
            form.fields[cls.get_post_name(field) + "groupend"].required = False #field.required
            
            form.fields[cls.get_post_name(field) + "groupend"].is_group = True #template knows to hide label display
            form.fields[cls.get_post_name(field)].is_group = True
            


        #=========================================================       
        else:
            #look for an anyvalue for this anyfield and set an initial value
            print "normal value starting " + str(field)

            #TODO: PUT MORE HERE! should test if rendering as calculated or not
            if field.calc and calc_mode != form.CALC_MODE_FORM:
                print "try calc"
                
                if calc_mode == form.CALC_MODE_PLAN:
                    form.fields[cls.get_post_name(field)].initial = field.calc.compile(base_group=calc_base_group, parent_class=calc_parent_class, plan_not_eval=True)
                    print form.fields[cls.get_post_name(field)].initial
                elif calc_mode == form.CALC_MODE_EVAL:
                    form.fields[cls.get_post_name(field)].initial = field.calc.compile(base_group=calc_base_group, parent_class=calc_parent_class, plan_not_eval=False)
                else:
                    raise CustomException("Invalid value for calc_mode " + calc_mode +". See defines in this class for valid values.")
                    
            else:                
                #not for calculating...
                try:
                    v = AnyValue.objects.filter(owner=owner).get(any_field=field)
                    form.fields[cls.get_post_name(field)].initial = v.get_value()
                        
                except ObjectDoesNotExist as detail:
                    print "failed! for field:" + str(field), detail #TODO: fix this... really crappy coding
                    form.fields[cls.get_post_name(field)].initial = ""
    
    
    #================================================================
    # ------------ save function ----------
    # loops thru fields and looks to see if there is a value object
    # for BOTH the same owner and any_field
    # If not, it creates a value object and links them. Otherwise,
    # it simply updates the existing one. 
    #================================================================
    def save(self, *args, **kwargs):   
        
        owner = AnyValueOwner.objects.get(id=self.cleaned_data["owner"])

        for i, field_name in enumerate(self.fields): #DO NOT REMOVE THE "i"!!! IT IS needed
            
            #don't process field for "owner" or f
            if field_name != "owner" and self.fields[field_name].is_group == False:
            
                any_field_id = self.post_name_2_ids(field_name)
                any_field = AnyField.objects.get(id=any_field_id)
                field_value = self.cleaned_data[field_name]
                #print dumpObj(field_value)
                
                #look for an anyvalue object that has same owner and AnyField
                v_query = AnyValue.objects.filter_by(owner=owner, any_field=any_field)
                count = v_query.count()

                #have to process choice fields differently
                #-----------------MULTIPLE_CHOICE_TYPE-----------------------
                if any_field.type == AnyField.MULTIPLE_CHOICE_TYPE:
                    
                    #find any other child value field (choice) for this parent field
                    kid_fields = AnyField.objects.get_children(any_field)
                
                    #1st mark all values as false
                    for kid in kid_fields:
                        #find any associated values for this child option
                        kid_values = AnyValue.objects.filter_by(owner=owner, any_field=kid)
                
                        #DO NOT DELETE these values as someone may be just changing setting from multiple to single playing around
                        #simply mark them as false
                        for v in kid_values:
                            v.update_value(0)
                    
                    #now loop thru list of values to set true and update values
                    for kid_field_id in field_value:
                        #try to find a value for this field and owner
                        q = AnyValue.objects.filter_by(owner=owner, any_field=kid_field_id)
                        
                        value = None #value to update, either found or created
                        
                        #if value already exists, just update it
                        if q.count() > 0:
                            if DEBUG and q.count() > 1:
                                raise #blah!!!
                            value = q[0]
                        #value not found, create it
                        else:
                            kid_field = AnyField.objects.get(id=kid_field_id)
                            value = AnyValue.new(AnyField.BOOLEAN_TYPE, owner, kid_field)
                        
                        #update the value now
                        value.update_value(1)                            
                    pass
                #-----------------SINGLE_CHOICE_TYPE-------------------------
                elif any_field.type == AnyField.SINGLE_CHOICE_TYPE:
                    #find any other child value field (choice) for this parent field
                    kid_fields = AnyField.objects.get_children(any_field)
                
                    #TODO: clean this up! gross gross gross... but works
                
                    for kid in kid_fields:
                        print "kid " + kid.title
                        #find all values for this child option
                        kid_values = AnyValue.objects.filter_by(owner=owner, any_field=kid)
                
                        #DO NOT DELETE these values as someone may be just changing setting from multiple to single playing around
                        #simply mark them as false
                        for v in kid_values:
                            v.update_value(0)
                                  
                        #mark the one that was selected as True
                        selected_child = AnyField.objects.get(id=field_value)
                        selected_children = AnyValue.objects.filter_by(owner=owner, any_field=selected_child)
                        if selected_children.count() > 0:
                            #TODO: this should check if more than 0 selected
                            selected_value = selected_children[0]
                        else:
                            #create new value
                            selected_value = AnyValue.new(AnyField.BOOLEAN_TYPE, owner, selected_child)                    

                        selected_value.update_value(1) #set it to True
                

                
                        
                #-----------------NORMAL TYPE OF FIELD-------------------------
                else:
                    #normal type of field
                    if count > 1:
                        raise  #error for more than one value field to point to both. TODO: exception class?
                    
                    #just update value, do not recreate it
                    if count == 1:
                        v = v_query[0]
                        v.update_value(field_value)                      
                    else:
                        #count == 0
                        v = AnyValue.new(any_field.type,owner,any_field);
                        v.update_value(field_value)
                
                        
    #========================================================    
    #provides a unique id for form processing for this field
    # form: <generic field id>
    @staticmethod
    def get_post_name(any_field):
        #return str(any_field.field_group.id) + "__" + str(any_field.id)
        return str(any_field.id)
    
    def post_name_2_ids(self, form_name):
        #(field_group_id, sep, any_field_id) = form_name.split("__")
        #return (field_group_id, any_field_id)
        return form_name
    
    #========================================================
    #translates the any_field into a Django form field object
    @staticmethod
    def field_2_formfield(any_field, *args, **kwargs):
        result = 0
    
        #...................................................
        if any_field.type == AnyField.DATE_TYPE:
            result = forms.DateField(label=any_field.title)

        elif any_field.type == AnyField.TIME_TYPE:
            result = forms.TimeField(label=any_field.title)

        #...................................................
        elif any_field.type == AnyField.DECIMAL_TYPE:
            result = forms.DecimalField(label=any_field.title, max_digits=AnyValue.DECIMAL_MAX_DIGITS, decimal_places=AnyValue.DECIMAL_PLACES)
            
        elif any_field.type == AnyField.INTEGER_TYPE:
            result = forms.IntegerField(label=any_field.title)
            
        elif any_field.type == AnyField.BOOLEAN_TYPE:
            result = forms.BooleanField(label=any_field.title)
        
        #...................................................
        elif any_field.type == AnyField.CHAR_TYPE:
            result = forms.CharField(label=any_field.title)
            
        elif any_field.type == AnyField.TEXT_TYPE:
            result = forms.fields.CharField(label=any_field.title, widget=forms.widgets.Textarea)                    
        
        #...................................................       
        elif any_field.type == AnyField.SINGLE_CHOICE_TYPE:
            choices = AnyField.objects.get_choices_for_parent(any_field)
            result = forms.ChoiceField(choices=choices, label=any_field.title)                    
        
        elif any_field.type == AnyField.MULTIPLE_CHOICE_TYPE:
            choices = AnyField.objects.get_choices_for_parent(any_field)
            result = forms.MultipleChoiceField(choices=choices, label=any_field.title, widget=forms.CheckboxSelectMultiple)
        
        #...................................................
        elif any_field.type == AnyField.GROUP_TYPE:
            result = forms.CharField(label=any_field.title, widget=FieldsetStartWidget(legend=any_field.title))
        
        #...................................................
        elif any_field.type == AnyField.FILE_TYPE:
            result = forms.FileField(label=any_field.title)
        
        else:
            raise CustomException("Invalid value for any_field.type " + str(any_field.type) +".")
        
        return result


    
#========================================================================
class Calc(models.Model):
    #allow it to aggregate
    #allow it to calculate
 
    #string version: sum(FM_income) + 
    formula = models.CharField(max_length = 200)  #pushed to lowercase for processing!!!!
    
    CMD_SUM = "sum"
    CMD_COUNT = "count" 
    CMD_NAMES = {CMD_SUM:CMD_SUM, CMD_COUNT:CMD_SUM} #used to validate and interpret commands
    
    def __unicode__(self):
        
        afs = "   ref by:"
        anyfields = self.anyfield_set.all()
        for af in anyfields:
            afs = afs + af.name + ", "
        return self.formula + afs
    
    #TODO: pass in owner, and date range that will apply to all un-scoped 
    def compile(self, **kwargs):
        expression = "" #string to be evaluated
        input = self.formula
        tokens = parse_equation(input)

        #this one is required
        parent_class = None
        try:
            parent_class = kwargs.pop('parent_class')  #this is a class to use for queries. For myewb use, it is a ProgramArea object
        except(KeyError):
            raise CustomException("need to pass a parent_class object like ProgramArea in parameters")

        plan_not_eval = None 
        if 'plan_not_eval' in kwargs:
            plan_not_eval = kwargs.pop('plan_not_eval')  #should be True or False. True = agg for plan. False = aggregate for eval. None = neither.

        base_group = None 
        if 'base_group' in kwargs:
            base_group = kwargs.pop('base_group')
        
        value_owner=None
        if 'value_owner' in kwargs:
            value_owner = kwargs.pop('value_owner')
        
        start_date=None
        if 'start_date' in kwargs:
            start_date = kwargs.pop('start_date')
     
        end_date=None
        if 'end_date' in kwargs:
            end_date = kwargs.pop('end_date')
        
        
        #loop thru all parsed tokens..........................
        for item in tokens:
            
            #if the token is a COMMAND......................................
            if item.__class__ == ParseCommand:

                #check for valid command name
                if not self.CMD_NAMES.has_key(item.command_name):
                    raise CustomException("Command does not exist " + item.command_name)
                
                #check for valid program areas, groups and field names
                pa = None
                try:
                    pa = parent_class.objects.get(slug=item.program_area)
                except(ObjectDoesNotExist):
                    raise CustomException("Missing or invalid program area " + item.program_area)
                
                fg = None
                if item.field_group != "": #allowed to be empty, but not invalid
                    fg = self.get_field_group(item.field_group, pa)
                else:
                    #field group is empty... find it based on plan_not_eval setting                     
                    try:
                        if plan_not_eval == True:
                            fg = pa.plan_model
                        elif plan_not_eval == False:
                            fg = pa.eval_model
                        else:
                            raise CustomException("plan_not_eval parameter must be set to True or False.")              
                    except(ObjectDoesNotExist):
                        raise CustomException("Looks like program area does not have it's plan/eval models setup correctly.")

                af = None
                try:
                    af = AnyField.objects.get(field_group=fg,name=item.field_name)
                except(ObjectDoesNotExist):
                    raise CustomException("Missing or invalid field group and/or field name" + item.field_group + ", " + item.field_name)
                      
                query = AnyValue.objects.filter(any_field=af)   #select all anyvalues for this field

                #TODO: select by date range and owner too               
                if base_group:
                    query = query.filter(owner__champinfo__event__parent_group=base_group)
                
                #made it this far... do it!
                active_field = AnyValue.cls_active_field(af) #figure out what to aggregate on as AnyValue has a mash of values
                
                #put in the conditional tests here
                #-------------------------------------------
                if item.condition.lower() == "if":
                    
                    cpa = pa  #cap = conditional program area
                    if item.conditional_program_area != "":
                        try:
                            cpa = parent_class.objects.get(slug=item.conditional_program_area)
                        except(ObjectDoesNotExist):
                            raise CustomException("Missing or invalid CONDITIONAL program area " + item.conditional_program_area)                       
                    
                    cfg = fg  #cfg = conditional field group
                    if item.conditional_field_group != "":
                        cfg = self.get_field_group(item.conditional_field_group, cpa)

                    caf = None  #caf for conditional any field
                    if item.conditional_any_field != "":
                        try:
                            caf = AnyField.objects.get(field_group=cfg, name=item.conditional_any_field)
                        except(ObjectDoesNotExist):
                            raise CustomException("Missing or invalid CONDITIONAL field group and/or field name: " + item.conditional_any_field)               
                    
               
                    if item.conditional_operator != "==" and item.conditional_operator != "=":
                        raise CustomException("Only == and = comparisons are supported right now")
                    
                    try:
                        caf = AnyField.objects.get(field_group=cfg, name=item.conditional_any_field)
                        query = query.filter(owner__anyvalue__any_field = caf, owner__anyvalue__integer = item.conditional_value)
                    except(ObjectDoesNotExist):
                        raise CustomException("Missing or invalid CONDITIONAL field group and/or field name: " + item.conditional_any_field)               
                
                #.................end of conditional tests
                
                
                if item.command_name == self.CMD_SUM:
                    query = query.aggregate(value=Sum(active_field))
                    v =query["value"]
                    print "v: " + repr(v)
                    expression = expression + str(v) + " "
                elif item.command_name == self.CMD_COUNT:
                    pass #TODO: do this!
                
                
            #end of if command-------------------------------------------- 
                
                
            elif item.__class__ == ParseOperation:
                expression += item.operation + " "  #no error checking here
            elif item.__class__ == ParseNumber:
                expression += str(item.value) + " "        
                
        #evaluate the expression
        safe_dict = dict()
        return eval(expression, {"__builtins__":None},safe_dict) 


    #..............................................
    @staticmethod
    def get_field_group(program_name, program_area):
        field_group = None
        if program_name == "plan": 
            field_group = program_area.plan_model
        elif program_name == "eval": 
            field_group = program_area.eval_model
        elif program_name == "goal":
            field_group = program_area.goal_model
        else:
            raise CustomException("Invalid field group. Must be either 'plan','eval', or 'goal' " + program_name)
        
        print "ZZZZ FIELD GROUP from get_field_group:" + str(field_group)
        return field_group

#========================================================================
    

#could be good!
#class MyModel(ModelForm):
#    m2m_field = forms.ModelMultipleChoiceField(queryset = SomeModel.objects.all(),
#                                               widget = forms.CheckboxSelectMultiple())

#==========================================================================
class AnyFieldManager(models.Manager):
    def get_choices_for_parent(self, parent_field):
        kids = self.get_children(parent_field)
        choices = list()
        
        for kid in kids:
            choices.append( (kid.id, kid.title  )  )
        return choices

    def get_children(self, parent_field):
        kids = self.filter(parent_field=parent_field).filter(visible=1).order_by('order')
        return kids

#==========================================================================
class AnyField(models.Model):
    objects = AnyFieldManager()

    #possible types. DO NOT change an existing one, but you can add new ones. should be ordered by number in admin. 
    DATE_TYPE       =    10
    TIME_TYPE       =    11
    #DATETIME_TYPE   =    12 not worth it in one type. Just use two fields.
            
    DECIMAL_TYPE    =    20
    INTEGER_TYPE    =    21
    BOOLEAN_TYPE    =    22
            
    CHAR_TYPE       =    30
    TEXT_TYPE       =    31
    
    SINGLE_CHOICE_TYPE = 40
    MULTIPLE_CHOICE_TYPE = 41

    LOCAL_CALC_TYPE = 50    #doesn't allow a field to be entered. Uses js to adjust value in real time. Calculated by server for display. 
                            #Can only work on fields within same form (local).
    CALC_TYPE = 51          #can be used to aggregate, calculate...
    
    FILE_TYPE = 60
    
    GROUP_TYPE = 70

    FIELD_TYPE_CHOICES = (
        (DATE_TYPE,         'Date'),
        (TIME_TYPE,         'Time'),
        #(DATETIME_TYPE,     'Datetime field'),
        
        (DECIMAL_TYPE,      'Decimal'),
        (INTEGER_TYPE,      'Integer'),
        (BOOLEAN_TYPE,      'Boolean'),
        
        (CHAR_TYPE,         'Char'),
        (TEXT_TYPE,         'Text'),
        
        (SINGLE_CHOICE_TYPE,         'Single choice'),
        (MULTIPLE_CHOICE_TYPE,         'Multiple choice'),
        
        (CALC_TYPE,                 "Calculation"),
        (FILE_TYPE,                 "File input"),
        (GROUP_TYPE,                "Grouping"),    
    )

    CALC_ADD = 1
    CALC_SUBTRACT = 2
    CALC_DIVIDE = 3
    CALC_MULTIPLY = 4 
    
    CALC_CHOICES = (
        (CALC_ADD,              'Add'),
        (CALC_SUBTRACT,         'Subtract'),
        (CALC_DIVIDE,           'Divide'),
        (CALC_MULTIPLY,         'Multiply'),
    ) 

    field_group = models.ForeignKey(FieldGroup)

    name = models.CharField(max_length = 44, blank=True)
    title = models.CharField(max_length = 100)
    help_text = models.CharField(max_length = 300, blank=True)
    
    private = models.BooleanField(default=0)  #to restrict access to owning chapter
    visible = models.BooleanField(default=1)  #instead of deleting things
    required = models.BooleanField(default=1) #is this field required before submitting?
    copy = models.NullBooleanField(default=1, blank=True, null=True)     #if true, this field's value will be copied when larger event copied.
    
    order = models.IntegerField(blank=True, null=True)  #used for order_by
    type = models.IntegerField(choices=FIELD_TYPE_CHOICES, default=INTEGER_TYPE)
    parent_field = models.ForeignKey('self', blank=True, null=True) #this is a 
    calc = models.ForeignKey(Calc, blank=True, null=True, default=None)

#    calc_field_a = models.ForeignKey('self', blank=True, null=True, related_name='calc_a', default=None) #TODO: figure out better related names
#    calc_field_b = models.ForeignKey('self', blank=True, null=True, related_name='calc_b', default=None) #TODO: figure out better related names
#    calc_operation = models.IntegerField('calc', choices=CALC_CHOICES, blank=True, null=True, default=None)

    def __unicode__(self):
        return self.field_group.slug + "-" + self.name + "[" + self.type_short(self.type).lower() + "]"


    assoc_values = forms.ChoiceField(CALC_CHOICES)

#    def assoc_values(self):
#        result = None
#        
#        for av in self.anyvalue_set.all():
#            result = av #result + str(av.id) + '<a href="http://google.com">goodle"'
#        return result

    @classmethod
    def type_english(cls, type):
        for tuple in cls.FIELD_TYPE_CHOICES:
            if tuple[0] == type:
                return tuple[1]

    @classmethod
    def type_short(cls, type):
        for tuple in cls.FIELD_TYPE_CHOICES:
            if tuple[0] == type:
                return tuple[1][0:3]
                    
        return "unknown"

#=======================================
                
#=======================================
class AnyValueOwner(models.Model):
    
#    def __unicode__(self):
#        return "blah!"
    pass


class AnyValueManager(models.Manager):
    def filter_by(self, owner='', any_field='', id=""):  #parent_field=''):
        q = self
        
        if(owner != ''):
            q = q.filter(owner=owner)
        if(any_field != ""):
            q = q.filter(any_field=any_field)
        if(id != ""):
            q = q.filter(id=id)
#        if(parent_field != ""):                          value doesn't have a parent!
#            q = q.filter(parent_field=parent_field)
        
        return q

    def get_only_instance_by(self, **kwargs):
        q = self.filter_by(**kwargs)

        #tests to ensure validity while in debug
        if DEBUG:
            if q.count() > 1:
                raise #MORE THAN ONE value associated with unique any_field and owner set. This should never happen 
        
        return q[0] or None


#
class AnyValue(models.Model):
    objects = AnyValueManager()

    any_field = models.ForeignKey(AnyField)
    owner = models.ForeignKey(AnyValueOwner)
    type = models.IntegerField(choices=AnyField.FIELD_TYPE_CHOICES)
    #if type = DATE_TYPE, only date field should be accessible
    #if type = DATETIME_TYPE, both date and time field should be accessible
    
    DECIMAL_MAX_DIGITS = 10
    DECIMAL_PLACES = 2
    
    integer = models.IntegerField(blank=True,null=True)
    decimal = models.DecimalField(decimal_places = DECIMAL_PLACES, max_digits = DECIMAL_MAX_DIGITS, blank=True,null=True) #enough for 100 million and 2 decimal places
    
    date = models.DateField(blank=True,null=True)
    time = models.TimeField(blank=True,null=True)
    
    char = models.CharField(max_length = 50, blank=True)
    text = models.TextField(blank=True)
    
    copied = models.BooleanField(default = False) #if True, it means that this value was copied when the larger event was copied and needs to be confirmed as valid by a user before the event can be confirmed.

    #TODO: create accessor methods that check if this value type matches what is being accessed
    
    #====================================================================
    # shorthand for constructing with all required fields right here :)
    @staticmethod
    def new(type,owner,any_field):
        value = AnyValue()
        value.type = type
        value.owner = owner
        value.any_field = any_field        
        return value 
    
    #==========================================================
    def update_value(self, value):
        if self.type == AnyField.DATE_TYPE:
            self.date = value;
        elif self.type == AnyField.TIME_TYPE:
            self.time = value;
            
        elif self.type == AnyField.DECIMAL_TYPE:
            self.decimal = value;
        elif self.type == AnyField.INTEGER_TYPE:
            self.integer = value;
        elif self.type == AnyField.BOOLEAN_TYPE:
            self.integer = value;        

        elif self.type == AnyField.CHAR_TYPE:
            self.char = value;        
        elif self.type == AnyField.TEXT_TYPE:
            self.text = value;
        
        self.save()
    
    
    #==========================================================
    # used by Calc class to figure out what field it shoud be
    # using in the database calls
    @classmethod
    def cls_active_field(cls, any_field):
        if any_field.type == AnyField.DATE_TYPE:
            return "date"
        elif any_field.type == AnyField.TIME_TYPE:
            return "time"
            
        elif any_field.type == AnyField.DECIMAL_TYPE:
            return "decimal"
        elif any_field.type == AnyField.INTEGER_TYPE:
            return "integer"
        elif any_field.type == AnyField.BOOLEAN_TYPE:
            return "integer"       

        elif any_field.type == AnyField.CHAR_TYPE:
            return "char"     
        elif any_field.type == AnyField.TEXT_TYPE:
            return "text"

    def active_field(self):
        return self.cls_active_field(self.any_field)


    #==========================================================        
    def get_value(self):
        if self.type == AnyField.DATE_TYPE:
            return self.date
        elif self.type == AnyField.TIME_TYPE:
            return self.time
            
        elif self.type == AnyField.DECIMAL_TYPE:
            return self.decimal
        elif self.type == AnyField.INTEGER_TYPE:
            return self.integer
        elif self.type == AnyField.BOOLEAN_TYPE:
            return self.integer        

        elif self.type == AnyField.CHAR_TYPE:
            return self.char        
        elif self.type == AnyField.TEXT_TYPE:
            return self.text        
             
        return -66666666
    




#    
#class test_form(forms.Form):
#    select = forms.MultipleChoiceField(choices=AnyField.FIELD_TYPE_CHOICES, label="a title", widget=forms.CheckboxSelectMultiple)
#    