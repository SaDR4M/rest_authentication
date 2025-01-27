
# Create your views here.
# built-in imports
import re
import uuid
# django & rest imports
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK , HTTP_400_BAD_REQUEST , HTTP_404_NOT_FOUND
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.contrib.auth.hashers import make_password
# third party imports
from icecream import ic
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
# local imports
from account.models import User
from account.utils import  signin_user , signup_user , check_otp
from notifications.models import SmsCategory
from core.send_sms import send_sms
from core.make_call import make_call



class UserOTPApiView(APIView):
    """ 
    only check OTP with mobile number
    /otp_checker/
    """
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_description="Sending OTP to the user mobile",
        operation_summary="Sending OTP",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "mobile" : openapi.Schema(description="user mobile" , type=openapi.TYPE_STRING , minlength=11)
                # "with_call" : 
            },
            required=["mobile"]
        ),
        responses={
            200 : "OTP is sent to the user",
            400 : "Wrong mobile number format"
        }
    )
    def post(self, request):
        '''
        send OTP to the user with SMS or CALL
        save the OTP has hash
        '''
        # filtering user
        mobile = request.data.get("mobile")
        mobile_validate = re.search("^(0|0098|98|\+98)9(0[1-5]|[1 3]\d|2[0-2]|9[1 8 9])\d{7}$", mobile)
        if not mobile_validate:
            response_json = {
                'succeeded': False,
                'show': True,
                'en_detail': 'Mobile is not correct',
                'fa_detail': 'ساختار شماره تلفن همراه نادرست است',
            }
            return Response(response_json, status=HTTP_400_BAD_REQUEST)
        with_call = False
        if request.data.get("with_call") == 'true':
            with_call = True      
        otp = str(uuid.uuid4().int)[:5]
        # TODO Security: Dont send code in response
        req = {
            "mobile": mobile,
            "code" : otp,
        }  

        req.update({
            "succeeded": True,
        })
        
        key = f'OTP:{mobile}'
        if cache.get(key):  # pass the sms code sending if we already have send an sms to user
            return Response({
                "succeeded": False,
                "remain_time": cache.ttl(key),
                }, status=HTTP_200_OK)
            
        if with_call == True:
            req.update({
                "send_with" : "CALL"
                })
            make_call(
                request.data.get("mobile"),
                message = otp,
            )
        else:
            # NOTE create sms category objects otherwise it will cause an error
            sms_category_obj = SmsCategory.objects.filter(code=1).first()
            
            if sms_category_obj.isActive == True:
                sms_text = sms_category_obj.smsText.format(otp,otp)
                send_sms(
                    request.data.get("mobile"),
                    sms_text,
                    sms_category_obj.id,
                    sms_category_obj.get_sendByNumber_display(),
                    request.user.id,
                )
            req.update({
                "send_with": 'SMS',
                })
        ## TODO remove code from response
        user_exists = User.objects.filter(mobile=mobile).exists()
        req.update({
            "succeeded": True,
            "user_exists" : user_exists,
            "send_otp": True,
            "remain_time": 60,
        })
        ic(req)
        hashed_otp =  make_password(otp)
        cache.set(f'OTP:{mobile}', hashed_otp, 60)
        return Response(req, status=HTTP_200_OK)
    
    
    
class SignInApiView(APIView):
    """ 
    authentication view class for normal user , Login and signup
    /register_login/
    """
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_description="Checking the OTP that was sent to user with the entered OTP then Signup/in the user base on the user existence",
        operation_summary="Signup/in",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "mobile" : openapi.Schema(description="user mobile" , type=openapi.TYPE_STRING , minlength=11),
                "otp" : openapi.Schema(description="otp" , type=openapi.TYPE_STRING , minlength=5),
            },
            required=["mobile" , "otp"]
        ),

        responses={
            200: openapi.Response(
            description="user is logged in or signed up",
            examples={
                "application/json": {
                    "succeeded": True,
                    "Authorization" : "Access token",
                    "role" : 10
                    }
                }
            ),
            400 : "Wrong OTP or OTP is expired"
        }
    )
    def post(self,request):
        ''' login/sign up'''
        mobile = request.data.get("mobile")
        otp = request.data.get('otp')
        is_otp_correct = check_otp(mobile , otp)
        # if otp is not correct return response
        if isinstance(is_otp_correct , Response) :
            return is_otp_correct
        # user = User.objects.get(
        #         mobile = mobile
        #     )
        try :
            user = User.objects.get(
                mobile = mobile
            )
        except User.DoesNotExist :
            return Response(
                data = {"en_detail" : "user does not exist" , "fa_detail" : "کاربر وجود ندارد"},
                status=HTTP_404_NOT_FOUND
            )
        # sign in the user
        response = signin_user(request , user)
        
        # delete OTP cache if it is not expired yet
        if cache.get(f"OTP_TRY-{mobile}") : 
            cache.delete(f"OTP_TRY-{mobile}")
            
        return response                

class SignUpApiView(APIView):
    """ 
    authentication view class for normal user , Login and signup
    /register_login/
    """
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_description="Checking the OTP that was sent to user with the entered OTP then Signup the user base on the user existence",
        operation_summary="Signup/in",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "mobile" : openapi.Schema(description="user mobile" , type=openapi.TYPE_STRING , minlength=11),
                "otp" : openapi.Schema(description="otp" , type=openapi.TYPE_STRING , minlength=5),
                "birthday" : openapi.Schema(description="user birthday" , type=openapi.TYPE_STRING),
                "password" : openapi.Schema(description="user password" , type=openapi.TYPE_STRING),
                "email" : openapi.Schema(description="user email" , type=openapi.TYPE_STRING)
            },
            required=["mobile" , "otp" , "birthday"]
        ),

        responses={
            200: openapi.Response(
            description="user is logged in or signed up",
            examples={
                "application/json": {
                    "succeeded": True,
                    "Authorization" : "Access token",
                    "role" : 10
                    }
                }
            ),
            400 : "Wrong OTP or OTP is expired - invalid paramters"
        }
    )
    def post(self,request):
        ''' login/sign up'''
        mobile = request.data.get("mobile")
        otp = request.data.get('otp')
        is_otp_correct = check_otp(mobile , otp)
        # if otp is not correct return response
        if isinstance(is_otp_correct , Response) :
            return is_otp_correct
        # check again if that user exists or not 
        user = User.objects.filter(mobile = mobile)
        if user.exists() :
            return Response(
                data={"en_detail" : "user exists" , "fa_detail" : " کاربری با این مشخصات وجود دارد"} , 
                status=HTTP_400_BAD_REQUEST
                )
        # sign up the user
        response = signup_user(request)
        
        # delete OTP cache if it is not expired yet
        if cache.get(f"OTP_TRY-{mobile}") : 
            cache.delete(f"OTP_TRY-{mobile}")
            
        return response                
