from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST


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
            if related_model.filter(id=instance.id).exists():
                return Response(
                    {'errors': add_error_msg},
                    status=HTTP_400_BAD_REQUEST)
            related_model.add(instance)
            return Response(serializer.data)

        if not related_model.filter(id=instance.id).exists():
            return Response(
                {'errors': remove_error_msg},
                status=HTTP_400_BAD_REQUEST)
        related_model.remove(instance)

        return Response(status=HTTP_204_NO_CONTENT)
