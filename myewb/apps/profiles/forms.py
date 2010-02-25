"""myEWB profile forms

This file is part of myEWB
Copyright 2009 Engineers Without Borders (Canada) Organisation and/or volunteer contributors

Created on 2009-06-22
Last modified on 2009-12-29
@author Joshua Gorner, Francis Kung, Ben Best
"""
from settings import STATIC_URL
from datetime import date
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from profiles.models import MemberProfile, StudentRecord, WorkRecord
from creditcard.forms import PaymentForm, PaymentFormPreview, ProductWidget
from creditcard.models import Product
from uni_form.helpers import FormHelper, Submit, Reset
from uni_form.helpers import Layout, Fieldset, Row, HTML
from siteutils.models import Address

class ProfileForm(forms.ModelForm):
	"""Add/edit form for the MemberProfile class."""
	
	class Meta:
		model = MemberProfile
		exclude = ('name', 'location', 'user', 'blogrss', 'timezone', 'language',
			'twitter_user', 'twitter_password', 'current_login', 'last_login', 'login_count',
			'address_updated', 'membership_expiry', 'contact_info')
			
class StudentRecordForm(forms.ModelForm):
	"""Add/edit form for the StudentRecord class."""
	class Meta:
		model = StudentRecord
		exclude = ('user', 'network')
        
class WorkRecordForm(forms.ModelForm):
	"""Add/edit form for the StudentRecord class."""
	class Meta:
		model = WorkRecord
		exclude = ('user', 'network')
		
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ('content_type', 'object_id')

MEMBERSHIP_TYPES = (('studues', _("Student ($20)")),
				    ('produes', _("Professional ($40)")))

class MembershipForm(forms.Form):
	membership_type = forms.ChoiceField(choices=MEMBERSHIP_TYPES,
										widget=forms.RadioSelect)
	chapters = [('none', _('(none)'))]
	chapter = forms.ChoiceField(choices=chapters)
	
	helper = FormHelper()
	layout = Layout('membership_type')
	helper.add_layout(layout)
	submit = Submit('submit', 'Continue')
	helper.add_input(submit)
	helper.action = ''
	
	def __init__(self, *args, **kwargs):
		chapterlist = kwargs.pop('chapters', None)
		for chapter in chapterlist:
			print chapter
			self.base_fields['chapter'].choices.append((chapter.slug, chapter.chapter_info.chapter_name))
		
		super(MembershipForm, self).__init__(*args, **kwargs)
    
class MembershipFormPreview(PaymentFormPreview):
    username = None
	
    def parse_params(self, *args, **kwargs):
        self.username = kwargs['username']
        
    # this gets called after transaction has been attempted
    def done(self, request, cleaned_data):
    	response = super(MembershipFormPreview, self).done(request, cleaned_data)
    	
    	if response == None:
    		request.user.get_profile().pay_membership()
        	
        	message = loader.get_template("profiles/member_upgraded.html")
        	c = Context({'user': self.username})
        	request.user.message_set.create(message=message.render(c))
        	
        	return HttpResponseRedirect(reverse('profile_detail', kwargs={'username': self.username }))
        else:
        	f = self.form(request.POST)
        	f.trnError = response
        	f.clean
        	context = {'form': f, 'stage_field': self.unused_name('stage'), 'state': self.state}
        	return render_to_response(self.form_template, context, context_instance=RequestContext(request))
        	
class UserSearchForm(forms.Form):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    chapters = [('none', _('Any chapter'))]
    chapter = forms.ChoiceField(choices=chapters, required=False)
  
    def __init__(self, *args, **kwargs):
        chapterlist = kwargs.pop('chapters', None)
        
        self.base_fields['first_name'].initial = kwargs.pop('first_name', None)
        self.base_fields['last_name'].initial = kwargs.pop('last_name', None)
        
        for chapter in chapterlist:
            try:
                i = self.base_fields['chapter'].choices.index((chapter.slug, chapter.chapter_info.chapter_name))
            except ValueError:
                self.base_fields['chapter'].choices.append((chapter.slug, chapter.chapter_info.chapter_name))
        
        self.base_fields['chapter'].initial = kwargs.pop('chapter', None)

        super(UserSearchForm, self).__init__(*args, **kwargs)
        
class UserSelectionInput(forms.MultipleHiddenInput):
    """
    Used to select one or more users, which are shown as labels
    corresponding to the users' real names, but stored as hidden
    inputs (usernames) behind the scenes.
    """
    class Media:
        css = {
            "all": (STATIC_URL + 'css/user_selection.css',)
        }
        js = (STATIC_URL + 'js/user_selection.js',)

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []        
        users = []

        for v in value:
            u = User.objects.get(username=v)
            users.append(u)
        t = loader.get_template('profiles/user_selection_input.html')
        c = Context({'users': users, 'field_name': name})
        return mark_safe(t.render(c))
        
class UserField(forms.Field):
    widget = UserSelectionInput
        
class SampleUserSearchForm(forms.Form):
    to = UserField(required=False)
    cc = UserField(required=False)
    bcc = UserField(required=False)
