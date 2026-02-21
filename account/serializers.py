
# built in
# django & rest imports 
from rest_framework.serializers import ModelSerializer, Serializer, CharField
# third party
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