# whenever a hospital gets saved (staff updates their beds, admin edits
# something, whatever), push the new numbers out to everyone connected
# to the live hospital feed.

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .consumers import HOSPITAL_UPDATES_GROUP
from .models import Hospital


@receiver(post_save, sender=Hospital)
def broadcast_hospital_update(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        # channel layer isn't configured (shouldn't happen given our
        # settings, but don't crash the save if it's somehow missing)
        return

    payload = {
        'id': instance.id,
        'name': instance.name,
        'is_active': instance.is_active,
        'total_beds': instance.total_beds,
        'available_beds': instance.available_beds,
        'total_icu_beds': instance.total_icu_beds,
        'available_icu_beds': instance.available_icu_beds,
        'available_ambulance_count': instance.available_ambulance_count,
    }

    async_to_sync(channel_layer.group_send)(
        HOSPITAL_UPDATES_GROUP,
        {'type': 'hospital_update', 'data': payload},
    )