# push the new status out to whoever's watching this specific request
# whenever it changes (accepted, dispatched, completed, cancelled...)

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AmbulanceRequest


@receiver(post_save, sender=AmbulanceRequest)
def broadcast_request_update(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    payload = {
        'id': instance.id,
        'status': instance.status,
        'hospital_name': instance.hospital.name if instance.hospital else None,
        'ambulance_number': instance.assigned_ambulance.vehicle_number if instance.assigned_ambulance else None,
        'accepted_at': instance.accepted_at.isoformat() if instance.accepted_at else None,
        'dispatched_at': instance.dispatched_at.isoformat() if instance.dispatched_at else None,
        'completed_at': instance.completed_at.isoformat() if instance.completed_at else None,
        'cancelled_at': instance.cancelled_at.isoformat() if instance.cancelled_at else None,
    }

    async_to_sync(channel_layer.group_send)(
        f'ambulance_request_{instance.id}',
        {'type': 'request_update', 'data': payload},
    )