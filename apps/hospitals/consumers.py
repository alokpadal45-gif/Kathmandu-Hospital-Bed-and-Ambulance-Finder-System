# websocket consumer for the live hospital list. every connected citizen
# joins the same group, and gets pushed a small update whenever ANY
# hospital's bed/icu/ambulance numbers change. the frontend js just needs
# to find the matching hospital card by id and update the numbers on it.

import json

from channels.generic.websocket import AsyncWebsocketConsumer

HOSPITAL_UPDATES_GROUP = 'hospital_updates'


class HospitalAvailabilityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(HOSPITAL_UPDATES_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(HOSPITAL_UPDATES_GROUP, self.channel_name)

    # name has to match the "type" key sent in group_send (see signals.py)
    async def hospital_update(self, event):
        await self.send(text_data=json.dumps(event['data']))