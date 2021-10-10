import base64
import re
from io import BytesIO

from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers
from rest_framework.pagination import (
    PageNumberPagination as DRFPageNumberPagination)
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST


class PageNumberPagination(DRFPageNumberPagination):
    page_size_query_param = 'limit'


class ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        data = re.search(r'(?<=data:)(.+);base64,(.+)$', data)
        if data is None:
            self.fail('invalid')
        content_type, file = data.groups()
        file_format = content_type.split('/')[1]
        file_name = self.context.get('request').data.get('name')
        full_name = f'{file_name}.{file_format}'
        file = base64.b64decode(file)
        file_size = len(file)
        file = BytesIO(file)
        data = UploadedFile(
            file=file,
            name=full_name,
            content_type=content_type,
            size=file_size,
            charset=None
        )
        return super().to_internal_value(data)


class RelEntryAddRemoveMixin:
    def rel_entry_add_remove(self, request, related_name,
                             add_error_msg, remove_error_msg):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        user = request.user
        related_model = getattr(user, related_name)

        if request.method == 'GET':
            if related_name == 'subscribed' and user == instance:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=HTTP_400_BAD_REQUEST)
            if instance in related_model.all():
                return Response(
                    {'errors': add_error_msg},
                    status=HTTP_400_BAD_REQUEST)
            related_model.add(instance)
            return Response(serializer.data)

        if instance not in related_model.all():
            return Response(
                {'errors': remove_error_msg},
                status=HTTP_400_BAD_REQUEST)
        related_model.remove(instance)

        return Response(status=HTTP_204_NO_CONTENT)
