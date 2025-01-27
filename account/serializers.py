
# built in
# django & rest imports 
from rest_framework.serializers import ModelSerializer
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

       
# class UserProfileInfoSerializer(ModelSerializer):

#     # office = OfficeSerializer(read_only=True)
#     # common_access_level = simpleCommonAccessLevelSerializer(read_only=True)
#     city = CityShowSerializerForUser()
#     state = StateShowSerialzerForUser()
#     last_login = SerializerMethodField('get_last_login')
#     my_membership = SerializerMethodField('get_my_membership')
#     my_cert = SerializerMethodField('get_my_cert')
#     def get_last_login(self, obj):
#         log = User_log.objects.filter(user = obj).last()
#         ser = UserLogSerializerBRF(log)
#         return ser.data
#     def get_my_membership(self,obj):
#         if obj.employee_of is not None:
#             user_obj = User.objects.get(id = obj.employee_of.id)
#             member = user_obj.last_plan
#         else:
#             member = obj.last_plan        
#         if member:
#             #member_obj = Membership.objects.get(id = member.id)
#             return MemberShipSerializer(member).data
#         return 'None'
    
#     def get_my_cert(self,obj):
#         if obj.employee_of is not None:
#             user_obj = User.objects.get(id = obj.employee_of.id)
#             cert = user_obj.last_cert
#         else:
#             cert = obj.last_cert
#         if cert:
#             return CompanyCertFullSerializer(cert).data
#         return 'None'        
        
#     class Meta:
#         model = User
#         fields = '__all__'
        
