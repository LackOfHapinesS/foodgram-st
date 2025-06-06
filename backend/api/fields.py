import base64

import rest_framework.serializers as slz
from django.core.files.base import ContentFile


class Base64ImageField(slz.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'img.{ext}')
        return super().to_internal_value(data)
