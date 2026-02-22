# django & rest imports 
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.serializers import ModelSerializer, Serializer, CharField
from rest_framework.validators import ValidationError
# third party
from icecream import ic
# local
from account.models import User
from account.models import UserLog

class UserSimpleSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'mobile', 'name', 'family_name', 'is_active', 'is_real']
        
class UserLogSerializerBRF(ModelSerializer):
    class Meta:
        model = UserLog
        fields = "__all__"   
           
class UserProfileCompletionSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"     
              
class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {
                'write_only': True,
            },
            'temp_password': {
                'write_only': True,
            }
        }

class UserPasswordUpdateSerializer(Serializer):
    old_password = CharField(allow_blank=False)
    new_password = CharField(allow_blank=False)
    confirm_password = CharField(allow_blank=False) 

    class Meta:
        fields = [
            "old_password",
            "new_password",
            "confirm_password"
        ]

    def validate(self, data, *args, **kwargs):

        current_password = self.context.get("password", "")
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not current_password:
            raise ValidationError("Password must be set")

        if old_password != confirm_password:
            raise ValidationError("Passwords must match")

        if not check_password(old_password , current_password) :
            raise ValidationError("Invalid password")
            
        # user cannot set the old password as new password
        if old_password == new_password :
            raise ValidationError("Current password cannot be set as new password")

        return super().validate(attrs=attrs)