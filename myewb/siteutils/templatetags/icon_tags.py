import os

from django import template
from django.conf import settings

register = template.Library()

KNOWN_EXTENSIONS = (
        'doc',
        'xls',
        'docx',
        'pdf',
        'jpg',
        'png',
        'gif',
)

def icon_for_filename(filename):
    """
    Looks at the extension on the filename and returns the
    extension if it is known, and file otherwise in order to render
    an image icon for the filetype.
    """
    (shortname, extension) = os.path.splitext(filename)
    extension = extension.lower().strip('.')
    # assume our icons are named <extension>.png
    if extension not in KNOWN_EXTENSIONS:
        extension = 'file'
    return {
            'STATIC_URL': settings.STATIC_URL,
            'extension': extension,
            }
register.inclusion_tag('icon_tags/filetype_icon.html')(icon_for_filename)

IMAGE_EXTENSIONS = (
        'jpg',
        'png',
        'gif',
)

# doesn't really fit.. should rename this to "attachment_helper_tags" or something,
# and combine with filesize_tags
def image_preview(filepath, filename, postid):
    """
    Looks at the extension on the filename and provides a javascript preview
    if it is a recognized image
    """
    (shortname, extension) = os.path.splitext(filename)
    extension = extension.lower().strip('.')
    preview = False
    if extension in IMAGE_EXTENSIONS:
        preview = True
        
    return {'preview': preview,
            'STATIC_URL': settings.STATIC_URL,
            'filepath': filepath,
            'postid': postid
            }
register.inclusion_tag('icon_tags/image_preview.html')(image_preview)
