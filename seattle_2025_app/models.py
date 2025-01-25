from django.contrib.auth import get_user_model
from django.db import models

UserModel = get_user_model()


class ControllPerson(models.Model):
    class Meta:
        # we need indexes on both fields for fast lookups
        indexes = [
            models.Index(fields=["perid"]),
            models.Index(fields=["newperid"]),
        ]

    perid = models.IntegerField(null=True, unique=True)
    newperid = models.IntegerField(null=True, unique=True)

    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name="controll_person"
    )
