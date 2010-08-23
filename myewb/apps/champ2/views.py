# Create your views here.
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse #????needed for finding absolute url of a named url in url.py. reverse("index") = "127.0.0.1:8000/"
from django.core.exceptions import ObjectDoesNotExist


import datetime

#
from champ2.helper import matrice_value_set_incomplete_count, matrice_value_set_invalid_count, matrice_program_area_incomplete_count

#
from events.models import Event
from networks.models import Network
from base_groups.decorators import group_admin_required   #this is a test if exec. Note: must be used like"@group_admin_required()" don't forget the "()"
from django.contrib.auth.decorators import login_required 

#import your needed models here
from flexmodel.models import *
from champ2.models import *
from champ2.forms import getProgramAreasForm, ProgramAreaCheckBoxForm, MatriceProgramAreaForm



from django.forms.forms import Form
from django import forms

from django.template.defaultfilters import slugify
from django.db.models.base import Empty
from httplib import HTTPResponse

#from champs.dprint import dumpObj  #for fancy debug printing

domain = "http://127.0.0.1:8000"



#==============================================================================================
"""
nested forms have to be named so that the following works: form.subform.is_valid()
    aka: the nested form has to be named "subform"
"""
class FormGroup():
    
    def __init__(self):
        self.forms = list()
    
    def add_form(self,form):
        self.forms.append(form)

    def is_valid(self):
        result = True
        
        print "FORSLKEWLEKFMWE"
        for form in self.forms:
            print form
            print form.is_valid()
            result = result and form.is_valid()
            
            #try validating any nested forms
            try:
                result = result and form.subform.is_valid()
            except(AttributeError):
                pass
        
        return result
    
    #TODO: could make this object iterable





#======================================================
#TEMPLATE to copy and paste from
#======================================================
def plan(request, event_id):
    my_template_data = dict()

    #TODO: put in authentication stuff

    #get champ_info for this event
    champ_info = ChampInfo.objects.get(event=event_id)

    #allow them to select which program types this event belongs to
    program_areas = ProgramArea.objects.all()
    formgroup = FormGroup()

    #add all forms for selected program areas    
    for i,pa in enumerate(program_areas):
        
        #note: field name is the name used in the template for rendering the checkbox widget
        form = ProgramAreaCheckBoxForm(request.POST or None, program_area=pa, champ_info=champ_info, owner=champ_info.value_owner, field_name="checkbox")
       
        form.groupname = pa.name
        field_group = pa.plan_model
        form.subform = FieldGroupForm(request.POST or None, field_group=field_group, owner = champ_info.value_owner)
        formgroup.add_form(form)
    
    my_template_data["formgroup"] = formgroup.forms
    
    
    #validate fields
    if request.POST:#formgroup.is_valid(): # check if fields validated

        valid = False
        #TODO... do not trust user entered data... should verify correctness here
        
        #loop thru formgroup and save stuff
        for form in formgroup.forms:
            
            #create or delete program link for corresponding checkbox
            q = ProgramLink.objects.filter(champ_info=champ_info, program_area=form.program_area)
            c = q.count()

            #if one or more program links exist
            if c > 0:
                if form.is_set(): #if checkbox set
                    c = c -1 #allow one program link to stay as check box is set, delete the rest though
                    print "THIS IS SET!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" + form.program_area.name
                    
                #delete any extras hanging around, but leave one program link
                for pl in q:
                    if c>0:
                        pl.delete()
            elif form.is_set():
                pl = ProgramLink()
                pl.champ_info = champ_info
                pl.program_area = form.program_area
                pl.save()
            
            if form.is_set():
                if form.subform.is_valid():
                    #process the subform for this program group from
                    form.subform.save()
            else:
                valid = False

#        return HttpResponseRedirect(domain + reverse(events) ) # Redirect after POST
        
        if valid:
            return HttpResponseRedirect(domain ) # Redirect after POST

    return render_to_response('champ2/event.html', my_template_data, context_instance=RequestContext(request))

#======================================================
#TEMPLATE to copy and paste from
#======================================================
def eval(request, event_id):
    my_template_data = dict()
    
    #TODO: put in authentication stuff

    #get champ_info for this event
    champ_info = ChampInfo.objects.get(event=event_id)

    #find which program areas this event has
    program_areas = ProgramArea.objects.filter(programlink__champ_info=champ_info)
    formgroup = FormGroup()

    #add all forms for selected program areas    
    for i,pa in enumerate(program_areas):
        
        form = Empty()
       
        form.groupname = pa.name
        form.program_area = pa
        field_group = pa.eval_model
        form.subform = FieldGroupForm(request.POST or None, field_group=field_group, owner = champ_info.value_owner)
        formgroup.add_form(form)
    
    my_template_data["formgroup"] = formgroup.forms
    
    
    #validate fields
    if request.POST:#formgroup.is_valid(): # check if fields validated

        valid = False
        #TODO... do not trust user entered data... should verify correctness here
        
        #loop thru formgroup and save stuff
        for form in formgroup.forms:
            
            if form.subform.is_valid():
                #process the subform for this program group from
                form.subform.save()
            else:
                valid = False

#        return HttpResponseRedirect(domain + reverse(events) ) # Redirect after POST
        
        if valid:
            return HttpResponseRedirect(domain ) # Redirect after POST

    return render_to_response('champ2/event.html', my_template_data, context_instance=RequestContext(request))

    


#======================================================
#TEMPLATE to copy and paste from
#======================================================
def base_group(request, network_slug):
    my_template_data = dict()
    
    #get base group
    network = Network.objects.get(slug=network_slug) #TODO: get or 404
       
    #get all events for this chater
#    events = Event.objects.filter(parent_group = network)
    events = network.events.all()
    s = ""
    
    for e in events:
        s = s + " " + str(e)
    
    return HttpResponse("hi there!" + s)
    
    return render_to_response('someTemplate.tpl', my_template_data, context_instance=RequestContext(request))

#======================================================
#
#======================================================
@group_admin_required()
#@login_required
def base_group_goals(request, group_slug):
    my_template_data = dict()
    
    network = BaseGroup.objects.get(slug=group_slug)
    
    #get current matching date range
    date_range = DateRange.objects.filter(start__lte=datetime.date.today(), end__gte=datetime.date.today())[0] #TODO: can we guarantee non overlapping? 
    #TODO: if the date range fails... should email someone saying... put this in!
    
    values_owner = None
    
    #get Goal object for this network or create it if it does not exist 
    try:
        goal = Goal.objects.get(date_range=date_range, base_group=network)
        values_owner = goal.values_owner
    except(ObjectDoesNotExist):
        goal = Goal()
        goal.date_range = date_range
        goal.base_group = network
        values_owner = AnyValueOwner()
        values_owner.save()
        goal.values_owner = values_owner 
        goal.save()
    
    #show goals for all the goal forms


    #allow them to select which program types this event belongs to
    program_areas = ProgramArea.objects.all()
    formgroup = FormGroup()
    
    #add all forms for selected program areas    
    for i,pa in enumerate(program_areas):
        form = Empty()
        form.groupname = pa.name
        field_group = pa.goal_model #the model to render
        form.subform =  FieldGroupForm(request.POST or None, field_group=field_group, owner = values_owner, calc_base_group=network, calc_parent_class=ProgramArea)
        form.plan =     FieldGroupForm(request.POST or None, field_group=field_group, owner = values_owner, calc_base_group=network, calc_parent_class=ProgramArea, calc_mode=FieldGroupForm.CALC_MODE_PLAN, extra_prefix="planz") 
        form.eval =     FieldGroupForm(request.POST or None, field_group=field_group, owner = values_owner, calc_base_group=network, calc_parent_class=ProgramArea, calc_mode=FieldGroupForm.CALC_MODE_EVAL, extra_prefix="evals")
        
        formgroup.add_form(form)
    
    my_template_data["formgroup"] = formgroup.forms
    
    #validate fields
    if request.POST:#formgroup.is_valid(): # check if fields validated

        valid = False
        #TODO... do not trust user entered data... should verify correctness here
        
        #loop thru formgroup and save stuff
        for form in formgroup.forms:

            if form.subform.is_valid():
                #process the subform for this program group from
                form.subform.save()

#        return HttpResponseRedirect(domain + reverse(events) ) # Redirect after POST
        
        if valid:
            return HttpResponseRedirect(domain ) # Redirect after POST

    return render_to_response('champ2/goal.html', my_template_data, context_instance=RequestContext(request))
    
        


#======================================================
#
#======================================================
def base_group_goals_date(request, group_slug, date_range_slug):
    my_template_data = dict()

    pass

#=============================================================
#show them a page of all matrice goals and entries by date
def matrices_group(request, group_slug): 
    my_template_data = dict()

    base_group = BaseGroup.objects.get(slug=group_slug)
    dates = MatriceDate.objects.all()
    

    sets = list()
    
    for date in dates:
        
        set = Empty()
        set.date = date
        
        #find any GOAL matrice value sets for the date and group
        try:
            vs = MatriceValueSet.objects.get(base_group=base_group, matrice_date=date, type=MatriceValueSet.GOAL_TYPE)
            set.goal = vs
        except(ObjectDoesNotExist):
            set.goal = None 

        #find any MEASURE matrice value sets for the date and group
        try:
            vs = MatriceValueSet.objects.get(base_group=base_group, matrice_date=date, type=MatriceValueSet.MEASUREMENT_TYPE)
            set.measurement = vs
        except(ObjectDoesNotExist):
            set.measurement = None
        
        if set.goal:
#            set.invalid_goal_count =  matrice_value_set_invalid_count(set.goal)                    #this doesn't currently make sense because no invalid values can be stored
            set.incomplete_goal_count =  matrice_value_set_incomplete_count(set.goal)
        
        if set.measurement:
#            set.invalid_measurement_count =  matrice_value_set_invalid_count(set.measurement)      #this doesn't currently make sense because no invalid values can be stored
            set.incomplete_measurement_count =  matrice_value_set_incomplete_count(set.measurement)
       
        sets.append(set) 
                
    my_template_data["sets"] = sets

    return render_to_response('champ2/matrices_group.html', my_template_data, context_instance=RequestContext(request))

#======================================================
def matrices_group_goal_date(request, group_slug, date_range_slug):
    return matrices_group_date(request, group_slug, date_range_slug, True)
   
def matrices_group_measurement_date(request, group_slug, date_range_slug):
    return matrices_group_date(request, group_slug, date_range_slug, False)

@group_admin_required()
def matrices_group_date(request, group_slug, date_range_slug, is_goal):
    my_template_data = dict()
    
    matrice_date = MatriceDate.objects.get(slug=date_range_slug)
    base_group = BaseGroup.objects.get(slug=group_slug)    
    
    mvs_type = MatriceValueSet.MEASUREMENT_TYPE
    if is_goal:
        mvs_type = MatriceValueSet.GOAL_TYPE
        
    matrice_value_set = None
    try:
        matrice_value_set = MatriceValueSet.objects.get(base_group=base_group, matrice_date=matrice_date, type=mvs_type)
    except(ObjectDoesNotExist):
        matrice_value_set = MatriceValueSet()
        matrice_value_set.base_group = BaseGroup.objects.get(slug=group_slug)
        matrice_value_set.matrice_date = matrice_date
        matrice_value_set.type = mvs_type
        matrice_value_set.save()

    mall = Empty() #data object we will add stuff to. stands for matrice (m), all 
    mall.groups = list()

    mall.base_group_name = base_group.name
    mall.matrice_date = matrice_date

    #loop thru matrice groups
    matrice_groups = MatriceGroup.objects.all()
    for mg in matrice_groups:
        mg_context = Empty()
        mg_context.name = mg.title
        mg_context.program_areas = list()
               
        #loop thru program areas for groups
        for mpa in mg.program_areas.all():
            pa_context = Empty()
            
            #add form to context
            pa_context.name = mpa.title
            pa_context.id = mpa.id
            pa_context.form = MatriceProgramAreaForm(request=request.POST or None, matrice_value_set=matrice_value_set, matrice_program_area=mpa)
            pa_context.metrics_incomplete = matrice_program_area_incomplete_count(mpa, matrice_value_set)
    
            #save if valid
            if request.POST and pa_context.form.is_valid():
                pa_context.form.save()
                    
            #add program area to program areas list
            mg_context.program_areas.append(pa_context)
        
        #add group to groups list
        mall.groups.append(mg_context)

        #TODO: the URL to post new using AJAX is HARD CODED!!!! BAD!
    
    my_template_data["matrice_date"] = matrice_date
    my_template_data["base_group"] = base_group
    my_template_data["matrice_value_set"] = matrice_value_set
    my_template_data["is_goal"] = is_goal
    
    my_template_data["matrice_all"] = mall
    return render_to_response('champ2/matrices_form.html', my_template_data, context_instance=RequestContext(request))


#--------------------------------------------------------------------------------------------------------------------
def base_group_metrics_goal_ajax(request, group_slug, date_range_slug, metric_prog_area_id):
    return base_group_metrics_ajax(request, group_slug, date_range_slug, metric_prog_area_id, True)

def base_group_metrics_measurement_ajax(request, group_slug, date_range_slug, metric_prog_area_id):
    return base_group_metrics_ajax(request, group_slug, date_range_slug, metric_prog_area_id, False)
 
@group_admin_required()
def base_group_metrics_ajax(request, group_slug, date_range_slug, metric_prog_area_id, is_goal):
    my_template_data = dict()   

    mvs_type = MatriceValueSet.MEASUREMENT_TYPE
    if is_goal:
        mvs_type = MatriceValueSet.GOAL_TYPE

    matrice_date = MatriceDate.objects.get(slug=date_range_slug)
    base_group = BaseGroup.objects.get(slug=group_slug)

    matrice_value_set = None
    try:
        matrice_value_set = MatriceValueSet.objects.get(base_group=base_group, matrice_date=matrice_date, type=mvs_type)
    except(ObjectDoesNotExist):
        matrice_value_set = MatriceValueSet()
        matrice_value_set.base_group = BaseGroup.objects.get(slug=group_slug)
        matrice_value_set.matrice_date = matrice_date
        matrice_value_set.type = mvs_type
        matrice_value_set.save()

    mpa = MatriceProgramArea.objects.get(id=metric_prog_area_id)
    
    pa_context = Empty()
    pa_context.name = mpa.title
    pa_context.id = mpa.id
    pa_context.form = MatriceProgramAreaForm(request=request.POST or None, matrice_value_set=matrice_value_set, matrice_program_area=mpa)
    
    #save if valid
    if request.POST and pa_context.form.is_valid():
        pa_context.form.save()

    my_template_data["pa"] = pa_context
    print repr(request.POST) 
    #my_template_data["debug"] = repr(request.POST) + " matrice1_1-9 = [" + request.POST["matrice1_1-9"] + "]"
    
    return render_to_response('champ2/matrices_form_ajax.html', my_template_data, context_instance=RequestContext(request))

#......................................
@group_admin_required()
def ajax_matrice_program_area_metrics_left(request, group_slug, metric_prog_area_id, metric_value_set_id):
    result = matrice_program_area_incomplete_count( MatriceProgramArea.objects.get(id = metric_prog_area_id), MatriceValueSet.objects.get(id=metric_value_set_id) ) 
    print "  ........ rez:"  + str(result)
    return HttpResponse(result)


#======================================================
#TEMPLATE to copy and paste from
#======================================================
def someView(request):
    my_template_data = dict()
    
    
    return render_to_response('someTemplate.tpl', my_template_data, context_instance=RequestContext(request))
