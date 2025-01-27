# built-in
import datetime
from user_agents import parse
# django & rest imports
from django.core.cache import cache
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.status import HTTP_200_OK , HTTP_400_BAD_REQUEST
# third party
# local imports
from account.models import UserLog
from account.serializers import UserSerializer
from core.ems import validation_error

def create_user_log(user_obj, request, kind):
    ''' based on the action (login, wrong pass and ...) we create a log for user and save the ip address and user agent info'''
    
    user_agent = request.headers.get("User-Agent")
    user_agent_spilited = parse(user_agent)
    browser = f"by browser {user_agent_spilited.browser.family} / version {user_agent_spilited.browser.version_string}"
    os = f"by os {user_agent_spilited.os.family} / version {user_agent_spilited.os.version_string}"
    device = f"by device {user_agent_spilited.device.family} /brand {user_agent_spilited.device.brand} model {user_agent_spilited.device.model}"
    for_admin = str(user_agent_spilited)
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")

    user_log = UserLog.objects.create(
        log_kind=kind,  # Wrong Password
        browser=browser,
        os=os,
        device=device,
        ip_address=ip,
        for_admin=for_admin,
        user=user_obj,
    )
    user_log.save()
    
    
def check_user_birthday(user) :
        today = datetime.date.today()
        today_is_birthday = False
        # set year to 1 check the month an day
        a = user.birthday.replace(year=1)
        b = today.replace(year=1)
        if user.last_login:
            last_login = user.last_login.date()
            if last_login < today and  a == b:
                today_is_birthday = True
        else:
            if a == b:
                today_is_birthday = True
        return today_is_birthday
    
    
def signin_user(request , user_obj) :
    """sign in user"""
    refresh = RefreshToken.for_user(user_obj)
    # check user birthday 
    today_is_birthday = check_user_birthday(user_obj)
    need_complete_profile = user_obj.need_complete       
    # user should change their password if they login successfully via this method. so:
    user_serialized = UserSerializer(
        user_obj,
        data ={"last_login": timezone.now()},
        partial=True,
        )
    if not user_serialized.is_valid():
        return validation_error(user_serialized)
    user_serialized.save()
    # successful login
    response_json = {
        "succeeded": True,
        "Authorization": 'Token '+str(refresh.access_token),
        "role": user_obj.role,
        "today_is_birthday": today_is_birthday,
    }
    # user log for LOGIN
    create_user_log(user_obj, request, kind=0)

    return Response(response_json, status=HTTP_200_OK)
    
    
def signup_user(request) :
    """signup user"""
    # check user birthday , role and mobile if there is one missing signup will be fail
    birthday = request.data.get("birthday")
    role = request.data.get("role")
    mobile = request.data.get("mobile")
    # if not birthday or role or mobile :
    #     return Response(
    #         data = {
    #             "succeeded" : False,
    #             "detail" : "birthday/role/mobile must be entered"  
    #         } ,
    #         status = HTTP_400_BAD_REQUEST
    #     )
    # user data
    # OPTIONAL data 
    password = make_password(request.data.get("password"))
    email = request.data.get("email")
    req = {
        "password": password,
        "birthday": birthday,
        "mobile": mobile,
        # NOTE becareful with this role if client pass ADMIN role the ADMIN user will be created
        "role": role,
        "email": email,
        "is_active": True, 
        "is_real": 1,
        "last_login": timezone.now()
    }
        
    user_serialized = UserSerializer(data=req)
    if not user_serialized.is_valid():
        return validation_error(user_serialized)
    # create user instance
    user_obj = user_serialized.save()  
    # create token
    token = RefreshToken.for_user(user_obj)
    # create log for LOGIN
    create_user_log(user_obj, request, kind=0)
        
    # TODO Security:  dont send Authorization TOKEN
    response_json = {
        "succeeded": True,
        "Authorization": f'Token {token.access_token}',
        "role": user_obj.role,
    }
        
    return Response(response_json, status=HTTP_200_OK)    

def check_otp(mobile , otp) :
    hashed_otp = cache.get(f"OTP:{mobile}")
    # otp has expired

    if not hashed_otp:
        return Response({
            "succeeded": False,
            'expired': True,
            'en_detail' : 'Get OTP code again.',
            'fa_detail' : 'مجدد درخواست کد دو عاملی داده شود', 
            'show': True  
            }, status=HTTP_400_BAD_REQUEST)

    # wrong otp
    if not check_password(otp , hashed_otp):
        return Response({
            "succeeded": False,
            'wrong_auth': True,
            'en_detail' : 'Get OTP code again.',
            'fa_detail' : 'مجدد درخواست کد دو عاملی داده شود', 
            'show': True 
            }, status=HTTP_400_BAD_REQUEST)
    return True