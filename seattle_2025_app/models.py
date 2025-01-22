from django.contrib.auth import get_user_model
from django.db import models

UserModel = get_user_model()


class ControllPerson(models.Model):
    perid = models.IntegerField(null=True, unique=True)
    newperid = models.IntegerField(null=True, unique=True)

    user = models.OneToOneField(
        UserModel, on_delete=models.CASCADE, related_name="controll_person"
    )
