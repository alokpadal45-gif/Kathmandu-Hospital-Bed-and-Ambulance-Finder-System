# per-request websocket - a citizen watching their own request's status
# page connects here and gets pushed the new status the moment hospital
# staff accept/dispatch/complete it. one group per request id so people
# only get updates for the request they're actually looking at.

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class AmbulanceRequestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.request_id = self.scope['url_route']['kwargs']['request_id']
        self.group_name = f'ambulance_request_{self.request_id}'

        user = self.scope['user']
        if not user.is_authenticated or not await self._user_can_view(user, self.request_id):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def request_update(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def _user_can_view(self, user, request_id):
        # only the citizen who made the request, or hospital staff/admin,
        # should be able to watch it - stops someone guessing a request id
        # and snooping on a stranger's emergency
        from .models import AmbulanceRequest

        try:
            req = AmbulanceRequest.objects.get(pk=request_id)
        except AmbulanceRequest.DoesNotExist:
            return False

        if user.is_citizen:
            return req.citizen_id == user.id
        return user.is_hospital_staff or user.is_admin_role