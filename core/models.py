from django.db import models

# Create your models here.
class TimeStampedModel(models.Model):

    created = models.DateTimeField(auto_now_add=True, blank= True, null= True)
    modified = models.DateTimeField(auto_now=True, blank= True, null= True)

    class Meta:
        abstract = True