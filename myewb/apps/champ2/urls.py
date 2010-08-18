from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list

urlpatterns = patterns('',
#    url(r'^$', view='events.views.all', name="events_all"),
    url(r'^plan/(?P<event_id>\d+)/$', view='champ2.views.plan', name='champ2_plan'),
    url(r'^eval/(?P<event_id>\d+)/$', view='champ2.views.eval', name='champ2_eval'),
    
    url(r'^(?P<network_slug>[a-zA-Z]+)/$', view='champ2.views.network', name='champ2_network'),
    url(r'^(?P<network_slug>[a-zA-Z]+)/goals/$', view='champ2.views.network_goals', name='champ2_network_goals'),
    url(r'^(?P<network_slug>[a-zA-Z]+)/goals/(?P<date_range_slug>[a-zA-Z0-9_-]+)$', view='champ2.views.network_goals_date', name='champ2_network_goals_date'),
    
    
)
