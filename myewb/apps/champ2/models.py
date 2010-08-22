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


#=========================================================================================
#------MATRICE DEFINITION MODELS----------------------------------------------------
#=========================================================================================

#....................................................
class MatriceGroup(models.Model):
    order = models.IntegerField()
    slug = models.SlugField()
    title = models.CharField(max_length=40)

    def __unicode__(self):
        return str(self.order) + ". " + self.title

#....................................................
class MatriceProgramArea(models.Model):
    matrice_group = models.ForeignKey(MatriceGroup, related_name="program_areas")
    order = models.IntegerField()
    slug = models.SlugField()
    title = models.CharField(max_length=40)

    def __unicode__(self):
        return self.matrice_group.__unicode__()+ " -> " + str(self.order) + ". " + self.title
#....................................................
class MatriceMetric(models.Model):
    matrice_program_area = models.ForeignKey(MatriceProgramArea, related_name="metrics")
    order = models.IntegerField()
    title = models.CharField(max_length=40)
    
    help1 = models.TextField(help_text="New lines will be replaced by single spaces so feel free to copy and paste from a pdf into here.")
    help2 = models.TextField(help_text="New lines will be replaced by single spaces so feel free to copy and paste from a pdf into here.")
    help3 = models.TextField(help_text="New lines will be replaced by single spaces so feel free to copy and paste from a pdf into here.")
    help4 = models.TextField(help_text="New lines will be replaced by single spaces so feel free to copy and paste from a pdf into here.")
    
#    help1 = models.CharField(max_length=500)
#    help2 = models.CharField(max_length=500)
#    help3 = models.CharField(max_length=500)
#    help4 = models.CharField(max_length=500)

    def save(self, *args, **kwargs):
        self.help1 = self.formatHelpInput(self.help1)
        self.help2 = self.formatHelpInput(self.help2)
        self.help3 = self.formatHelpInput(self.help3)
        self.help4 = self.formatHelpInput(self.help4)
        super(MatriceMetric, self).save(*args, **kwargs)

    @staticmethod
    def formatHelpInput(text):
        text = text.replace("\r\n", " ")
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
        return text        

    def __unicode__(self):
        return self.matrice_program_area.__unicode__()+ " -> "  + str(self.order) + ". " + self.title
#....................................................
class MatriceDate(models.Model):
    title = models.CharField(max_length=20)
    slug = models.SlugField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __unicode__(self):
        return self.title + " " +  str(self.start_date) + "->" + str(self.end_date) 
#=========================================================================================
#----------MATRICE VALUE MODELS-----------------------------------------------------------
#=========================================================================================

#....................................................
#can be either a goal or a measurement
class MatriceValueSet(models.Model):
    
    MEASUREMENT_TYPE = 0
    GOAL_TYPE = 1
    
    TYPE_CHOICES = (
                    (MEASUREMENT_TYPE, "Measurement"),
                    (GOAL_TYPE, "Goal"),
                    )
    
    type = models.IntegerField(choices=TYPE_CHOICES)
    base_group = models.ForeignKey(BaseGroup)
    matrice_date = models.ForeignKey(MatriceDate)

    def is_goal(self):
        return self.type == self.GOAL_TYPE
    
    def is_measurement(self):
        return self.type == self.MEASUREMENT_TYPE

    def __unicode__(self):
        return self.base_group.name + " " + self.matrice_date.__unicode__() + " is_goal:" + str(self.is_goal())

#....................................................
class MatriceMetricValue(models.Model):
    matrice_metric = models.ForeignKey(MatriceMetric, related_name="values")
    matrice_value_set = models.ForeignKey(MatriceValueSet, related_name="values")
    value = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True) #value 1 to 4 allowing decimal values
    pass


    
