from django.db import models
from django.forms import ModelForm  #used for creating forms at bottom of page

from django.core.exceptions import ObjectDoesNotExist

from django.db.models import forms
#from champs.dprint import dumpObj  #for fancy debug printing

#from champs.settings import DEBUG

from flexmodel.models import FieldGroup, AnyValueOwner, AnyValue
from events.models import Event
from base_groups.models import BaseGroup

class CustomException(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class ProgramArea(models.Model):
    name = models.CharField(max_length = 100)
    slug = models.SlugField(help_text="Should be short like 'GE', 'PO'. This name used in calculation formulas do not change! ")
    plan_model = models.OneToOneField(FieldGroup) 
    eval_model = models.OneToOneField(FieldGroup, related_name="pa_eval") #TODO: related names suck... supposed to be 1 to 1
    goal_model = models.OneToOneField(FieldGroup, related_name="pa_goal") #TODO: related names suck... supposed to be 1 to 1
    #TODO: add in depreciated value for old program areas

    def __unicode__(self):
        return self.name

class ProgramLink(models.Model):
    champ_info = models.ForeignKey('ChampInfo')
    program_area = models.ForeignKey(ProgramArea)


class ChampInfoManager(models.Manager):
    #============================
    # returns true if a champ info object exists for an event
    def exists_by_event(self, event):
        print "exists_by_eventexists_by_eventexists_by_eventexists_by_event" + str(event)
        try:
            q = self.get(event=event)
            print "------------>EXISTS"
            return True
        except(ObjectDoesNotExist):
            print "------------>Does not EXIST so should create"
            return False #NOTE: This used to return None and wouldn't work!!!!
    

    #============================
    # returns true if a champ info object exists for an event
    def get_by_event(self, event):
        try:
            q = self.get(event=event)
            return q
        except(ObjectDoesNotExist):
            return None
    
class ChampInfo(models.Model):
    event = models.OneToOneField(Event)
    value_owner = models.OneToOneField(AnyValueOwner)

    objects = ChampInfoManager() #add a manager

    #====================================================================
    # shorthand for constructing with all required fields right here :) and saves it
    @staticmethod
    def new(event):
        champ_info = ChampInfo()
        champ_info.event = event
        value_owner = AnyValueOwner() #create and save value owner
        value_owner.save()
        print value_owner.id
        champ_info.value_owner = value_owner 
        champ_info.save()
        return champ_info
    
        

#these are created by admin for the available goals to be set by chapters 
class DateRange(models.Model):
    title = models.CharField(max_length=20)
    slug = models.CharField(max_length=20)
    start = models.DateField()
    end = models.DateField()

    def __unicode__(self):
        return str(self.start) + " to " + str(self.end)



class Goal(models.Model):    
    base_group = models.ForeignKey(BaseGroup)
    values_owner = models.ForeignKey(AnyValueOwner)
    date_range = models.ForeignKey(DateRange)
    #TODO: allow people responsible to associated here
    
    def __unicode__(self):
        return "Goal " + str(self.base_group) + " " + str(self.date_range)

