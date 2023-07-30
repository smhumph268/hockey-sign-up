from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.contrib.auth import get_user_model


# See https://stackoverflow.com/questions/61656796/how-do-i-set-a-user-as-inactive-in-django-when-registering
# Also see the Django Signals documentation
@receiver(pre_save, sender=get_user_model())
def set_new_regular_user_inactive(sender, instance, **kwargs):
    if instance._state.adding is True:
        if not instance.is_superuser:
            instance.is_active = False
