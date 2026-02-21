# django imports
from django.db.models import QuerySet
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from rest_framework.validators import ValidationError
from django.contrib.auth.password_validation import validate_password

class UserQuerySet(QuerySet):

    @staticmethod
    def is_password_valid(password: str):
        try :
            validate_password(password)
        except ValidationError as e:
            return False
        return True
class UserManager(BaseUserManager):
    """
    Custom user model manager where mobile is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, mobile, password, **extra_fields):
        """
        Create and save a User with the given mobile and password.
        """
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, mobile, password, **extra_fields):
        """
        Create and save a SuperUser with the given mobile and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(mobile,  password, **extra_fields)