from django import template
from django.conf import settings
from attachments.forms import AttachmentForm
from attachments.models import Attachment

register = template.Library()

def attachablecomments(context, obj):
    attach_forms = []       # for now, nothing by default
    return {
        'object': obj, 
        'request': context['request'],
        'user': context['user'],
        'attach_forms': attach_forms,
    }

register.inclusion_tag('threadedcomments/comments.html', takes_context=True)(attachablecomments)

# for some reason it doesn't load properly...
@register.simple_tag
def get_media_url():
    return settings.MEDIA_URL