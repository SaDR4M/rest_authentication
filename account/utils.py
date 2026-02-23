# built-in
import re
from user_agents import parse
from typing import Tuple
import uuid
# django & rest imports
from django.core.cache import cache
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.validators import ValidationError
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.status import HTTP_200_OK , HTTP_400_BAD_REQUEST
from django.core.cache import cache
from django.utils.timezone import datetime
# third party
from icecream import ic
# local imports
from account.serializers import UserSerializer
from core.ems import validation_error
from account.models.user_model import User
from account.models.user_log import UserLog



# for gurdian Anonymous user
def get_anonymous_user(User) : 
    anonymous_user , created = User.objects.get_or_create(
        id = 9999999999,
        defaults={
            "username" : "9999999999",
            "mobile" : "9999999999",
            "role" : 1
        }
    )
    if anonymous_user :
        return anonymous_user
    else :
        return created
    
    
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


def create_token(user:object) :
    """Create Refresh and access token for user"""
    token = RefreshToken.for_user(user)
    # login the user
    return dict(
        access_token = token.access_token,
        refresh_token = str(token)
    )
    
    
def create_otp(mobile) -> Tuple[bool, int]:
    # create otp code
    otp = str(uuid.uuid4().int)[:5]
    key = f'OTP:{mobile}'
        
    if cache.get(key):  # pass the sms code sending if we already have send an sms to user
        return False, cache.ttl(key)
    return True, int(otp)


def check_user_existence(mobile) :
    try :
        user = User.objects.get(mobile=mobile)
    except User.DoesNotExist:
        return Response(
            data = {
                "en_detail" : "Invalid mobile or password" ,
                "fa_detail" : "شماره یا رمز وارد شده اشتباه است"
                } ,
            status = HTTP_400_BAD_REQUEST)
    return user

    
def signin_user(request , user_obj) :
    """sign in user with OTP"""

    token = RefreshToken.for_user(user_obj)
    create_user_log(user_obj, request, kind=0)

    return dict(
        refresh=str(token),
        access=str(token.access_token)
    )
    
def signup_user(mobile: str) :

    """signup user"""
    hashed_password = make_password(password)
    req = {
        "password": hashed_password,
        "birthday": birthday,
        "mobile": mobile,
        "role": role,
        "is_active": True, 
        "is_real": is_real,
        "last_login": timezone.now()
    }   
    user_serialized = UserSerializer(data=req)
    if not user_serialized.is_valid():
        return validation_error(user_serialized)
    # create user instance 
    user_obj = user_serialized.save()  
    # create log for LOGIN
    create_user_log(user_obj, request, kind=0)
        
    # TODO Security:  dont send Authorization TOKEN
    response_json = {
        "succeeded": True,
    }
        
    return Response(response_json, status=HTTP_200_OK)    


def check_otp(mobile:str , otp:str) :
    
    hashed_otp = cache.get(f"OTP:{mobile}")
    # otp has expired or wrong otp
    if not hashed_otp or not check_password(otp , hashed_otp) :
        return False
    return True


def signin_user_wp(mobile:str , password:str , request:object) :
    """signin user with password and the mobile number"""
    # if there is no user with the mobile number
    # create token if the user exist and password is set

def validate_user_password(password:str) :
    """validate the password then update user password"""
    # validate new password => min len 8 , cannot be just numeric
    try :
        validate_password(password)
    except ValidationError as e:
        return Response(
            data = {
                "en_detail" : e.messages
            }
        )
    return True



def validate_user_mobile(mobile) :
    mobile_validate = re.search("^(0|0098|98|\+98)9(0[1-5]|[1 3]\d|2[0-2]|9[1 8 9])\d{7}$", mobile)
    if not mobile_validate:
        raise ValueError("Mobile is invalid")


def update_user_password(user:object , old_password:str , new_password:str , confirm_password:str ) :
    """update user password"""
    # for password change
    # the old password and user password are not same


def is_password_valid(password: str):
    try :
        validate_password(password)
    except ValidationError:
        return False
    return True