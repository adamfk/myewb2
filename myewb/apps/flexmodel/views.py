# Create your views here.
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse #????needed for finding absolute url of a named url in url.py. reverse("index") = "127.0.0.1:8000/"
from django.core.urlresolvers import resolve #????needed for finding absolute url of a named url in url.py. reverse("index") = "127.0.0.1:8000/"

#import your needed models here
from flexmodel.models import *

from champs.dprint import dumpObj  #for fancy debug printing

domain = "http://127.0.0.1:8000"

#================================================================================
# index
#================================================================================
def index(request):
    my_template_data = dict()

    #grab some data... do stuff
    #pass it all to the template

    fields = AnyField.objects.filter(field_group__id = 1).order_by('order')
    my_template_data["fields"] = fields
   
    c = Calc.objects.get(id=1)
    c.compile()
    
    # HELP??.. go here to learn about making more queries
    # http://docs.djangoproject.com/en/1.1/topics/db/queries/
    
    return render_to_response('index.tpl', my_template_data, context_instance=RequestContext(request))


#======================================================
#Example for how to deal with forms
#======================================================
def field_group(request, field_group_id):
    my_template_data = dict()
    
    field_group = FieldGroup.objects.get(id = field_group_id)
    owner = AnyValueOwner.objects.get(id=1) 
    form = FieldGroupForm(request.POST or None, field_group=field_group, owner = owner)

    my_template_data["form"] = form
    
    #validate fields
    if form.is_valid(): # check if fields validated

        #TODO... do not trust user entered data... should verify correctness here

        # Process the data in form.cleaned_data
        form_obj = form.save(commit=True) #save it to the db 

        return HttpResponseRedirect(domain + reverse(index) ) # Redirect after POST

    my_template_data["form"] = form; #pass the form to template as "form" variable
    my_template_data["page_to_receive_post_info"] = "." #the url to send posted form to. Ex: "127.0.0.1:8000/create" 

    return render_to_response('edit.tpl', my_template_data, context_instance=RequestContext(request))

def test(request):
    my_template_data = dict()
    


    return render_to_response('edit.tpl', my_template_data, context_instance=RequestContext(request))


#======================================================

#======================================================
def test_calc(request):
    
    formula = "blah!"

"""
    possible inputs:
    SUM(a_field) * AVG(b_field)
    a_field * 1.82 
    
    command:  \s*(?P<cmd>[A-Z]+)\(\s*(?P<field>[a-zA-Z_]+)\s*\)\s*
        must be uppercase
    
    field: \s*(?P<field>[a-zA-Z_]+)\s*
    
    operation: \s*(?P<op>[\+\-\*/])\s*
    
    number: \s*(?P<number>[0-9.])\s*

"""    
    
    
    
    
    # (?P<cmd>[A-Za-Z_]*)(
    
    





#======================================================
#page not found
#======================================================
def page_not_found(request):
    my_template_data = dict()
    
    return render_to_response('page_not_found.tpl', my_template_data, context_instance=RequestContext(request))





#======================================================
#TEMPLATE to copy and paste from
#======================================================
def someView(request):
    my_template_data = dict()
    
    
    return render_to_response('someTemplate.tpl', my_template_data, context_instance=RequestContext(request))
