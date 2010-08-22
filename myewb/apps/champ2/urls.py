from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list

urlpatterns = patterns('',
#    url(r'^$', view='events.views.all', name="events_all"),
    url(r'^plan/(?P<event_id>\d+)/$', view='champ2.views.plan', name='champ2_plan'),
    url(r'^eval/(?P<event_id>\d+)/$', view='champ2.views.eval', name='champ2_eval'),
    
    url(r'^(?P<group_slug>[a-zA-Z]+)/$', view='champ2.views.base_group', name='champ2_base_group'),
    url(r'^(?P<group_slug>[a-zA-Z]+)/goals/$', view='champ2.views.base_group_goals', name='champ2_base_group_goals'),
    url(r'^(?P<group_slug>[a-zA-Z]+)/goals/(?P<date_range_slug>[a-zA-Z0-9_-]+)$', view='champ2.views.base_group_goals_date', name='champ2_base_group_goals_date'),
    
    url(r'^matrices/(?P<group_slug>[a-zA-Z]+)/(?P<date_range_slug>[a-zA-Z0-9_-]+)/$', view='champ2.views.base_group_metrics', name='champ2_base_group_goals_date'),
    url(r'^ajax/matrices/(?P<group_slug>[a-zA-Z]+)/(?P<date_range_slug>[a-zA-Z0-9_-]+)/(?P<metric_prog_area_id>\d+)/$', view='champ2.views.base_group_metrics_ajax'),
    
)
