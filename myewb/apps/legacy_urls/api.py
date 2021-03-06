from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from emailconfirmation.models import EmailAddress
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden

urlpatterns = patterns('django.views.generic.simple',
    url(r'^posts/Any$', 'redirect_to', {'url': reverse('topic_feed_all'),
                                    'permanent': True}),
    url(r'^posts/Any plus Replies$', 'redirect_to', {'url': reverse('topic_feed_all'),
                                    'permanent': True}),
    url(r'^posts/(?P<tag>[-\w]+)$', 'redirect_to', {'url': '/feeds/posts/tag/%(tag)s/',
                                    'permanent': True}),
    url(r'^hot/Any$', 'redirect_to', {'url': reverse('topic_feed_featured'),
                                    'permanent': True}),
    url(r'^hot/Any plus Replies$', 'redirect_to', {'url': reverse('topic_feed_featured'),
                                    'permanent': True}),
    url(r'^list/(?P<group_slug>[-\w]+)$', 'redirect_to', {'url': '/feeds/posts/group/%(group_slug)s/',
                                    'permanent': True}),
    url(r'^calendar/(?P<group_slug>[-\w]+).ics$', 'redirect_to', {'url': '/events/ical/for/networks/network/slug/%(group_slug)s/',
                                    'permanent': True}),
    )

urlpatterns += patterns('legacy_urls.api',
    url(r'^login/null$', 'login'),
    )

def login(request):
    if request.method == 'POST':
        if request.POST.get('user', None) and request.POST.get('password', None) and \
        (request.META['REMOTE_ADDR'] == '127.0.0.1' or request.META['REMOTE_ADDR'] == '69.77.162.110'):
            
            username = request.POST['user']
            password = request.POST['password']
            
            if User.objects.filter(username=username).count() == 0:
                try:
                    email = EmailAddress.objects.get(email=username, verified=True)
                except :
                    return HttpResponse("false")
                username = email.user.username
                
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                return HttpResponse(str(user.id))

            return HttpResponse("false")
        
    return HttpResponseForbidden()
