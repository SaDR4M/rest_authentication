# built-in imports
import re
import uuid
# django & rest imports
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK , HTTP_400_BAD_REQUEST , HTTP_404_NOT_FOUND , HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated , AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
# third party imports
from icecream import ic
# local imports
from core.responses import ClientErrorResponse, ClientOkResponse
from core.roles import ADMIN_ROLE
from account.models import User
from account.utils import  (
    signin_user ,
    signup_user ,
    check_otp ,
    signin_user_wp ,
    update_user_password,
    validate_user_mobile,
    create_otp,
    create_token,
    create_user_log,
    is_password_valid
)
from account.serializers import UserSerializer, UserPasswordUpdateSerializer, ForgetPassSerializer
from notifications.models import SmsCategory
from core.send_sms import send_sms
from core.make_call import make_call
from account.docs import sign_in_otp_document , sign_up_document, sign_in_pass_document , update_credential_document , otp_document



class UserOTPApiView(APIView):
    """ 
    only check OTP with mobile number
    /otp_checker/
    """
    permission_classes = [AllowAny]
    @otp_document
    def post(self, request):
        '''
        send OTP to the user with SMS or CALL
        save the OTP has hash
        '''
        # filtering user
        # validate user mobile
        mobile = request.data.get("mobile")
        if not mobile:
            return ClientErrorResponse.invalid_paramter()

        try:
            validated_mobile = validate_user_mobile(mobile)
        except ValueError as e:
            return ClientErrorResponse.invalid_paramter(
                en_detail = 'Mobile is not correct',
                fa_detail = 'ساختار شماره تلفن همراه نادرست است',
            )
    
        with_call = False
        if request.data.get("with_call") == 'true':
            with_call = True      

        # create otp
        created, otp = create_otp(mobile)
        if not created:
            return ClientErrorResponse.invalid_paramter(
                fa_detail = f"زمان باقی مانده {cache.ttl(key)}",
            )
        
        # TODO Security: Dont send code in response
        req = {
            "succeeded": True,
            "mobile": mobile,
            "code" : otp,
        }  

        # send message for OTP
        # NOTE create sms category objects otherwise it will cause an error
        # FIXME fix this
        # sms_category_obj = SmsCategory.objects.filter(code=1).first()
        
        # if sms_category_obj.isActive == True:
        #     sms_text = sms_category_obj.smsText.format(otp,otp)
        #     send_sms(
        #         request.data.get("mobile"),
        #         sms_text,
        #         sms_category_obj.id,
        #         sms_category_obj.get_sendByNumber_display(),
        #         request.user.id,
        #     )
        user_exists = User.objects.filter(mobile=mobile).exists()
        req.update({
            "user_exists" : user_exists,
            "send_otp": True,
            "remain_time": 60,
        })
        ic(req)
        # save OTP
        hashed_otp =  make_password(str(otp))
        cache.set(f'OTP:{mobile}', hashed_otp, 120)
        return ClientOkResponse.ok_with_data(data=req)
    
    
    
class SignInApiView(APIView):
    """ 
    authentication view class for normal user , Login and signup
    """
    permission_classes = [AllowAny]
    @sign_in_otp_document
    def post(self,request):
        ''' login/sign up'''
        mobile = request.data.get("mobile")
        otp = request.data.get('otp')
        if not mobile or not otp:
            return ClientErrorResponse.invalid_paramter()

        is_otp_correct = check_otp(mobile , otp)
        if not is_otp_correct:
            return ClientErrorResponse.invalid_paramter(
                en_detail = "Get OTP code again.",
                fa_detail = "مجدد درخواست کد دو عاملی داده شود", 
            )

        try :
            user = User.objects.get_user_with_mobile(mobile=mobile)
        except User.DoesNotExist :
            return Response(
                data = {"en_detail" : "user does not exist" , "fa_detail" : "کاربر وجود ندارد"},
                status=HTTP_404_NOT_FOUND
            )

        # sign in the user
        tokens = signin_user(request , user)
        user_serialized = UserSerializer(
            user,
            data ={"last_login": timezone.now()},
            partial=True,
        )
        if not user_serialized.is_valid():
            return validation_error(user_serialized)
        user_serialized.save()

        # delete OTP cache if it is not expired yet
        if cache.get(f"OTP:{mobile}") : 
            cache.delete(f"OTP:{mobile}")
            
        return ClientOkResponse.ok_with_data(data=tokens)                


class SignUpApiView(APIView):
    """ 
    authentication view class for normal user , Login and signup
    """
    permission_classes = [AllowAny]
    @sign_up_document
    def post(self,request):
        ''' login/sign up'''
        mobile = request.data.get("mobile")
        otp = request.data.get('otp')
        password = request.data.get("password")
        # if otp is not correct return response
        if not check_otp(mobile, otp):
            return ClientErrorResponse.invalid_paramter(
                en_detail = "Get OTP code again.",
                fa_detail = "مجدد درخواست کد دو عاملی داده شود", 
            )

        # sign up the user
        if User.user_exist(mobile):
            return Response(
                data={
                    "en_detail" : "user exists" ,
                    "fa_detail" : "کاربری با این مشخصات وجود دارد"
                } , 
                status=HTTP_400_BAD_REQUEST
            )

        # validate user password
        if not is_password_valid(password):
            return ClientErrorResponse.invalid_paramter(
                fa_detail="پسورد معتبر نمیباشد"
            )
        
        # NOTE becareful with role if client pass ADMIN role the ADMIN user will be created
        hashed_password = make_password(password)
        request.data.update({
            "password": hashed_password,
            "last_login": timezone.now()
        })

        user_serialized = UserSerializer(data=request.data)
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
            
        if role == ADMIN_ROLE :
            return Response(status=403)

        # delete OTP cache if it is not expired yet
        cache.delete(f"OTP:{mobile}")
            
        return response                

# sign in the user with password
class SignInWithPassApiView(APIView):
    """
    authenticate user with mobile number and the password
    3 situations may occur
    1) mobile or password is wrong
    2) password is not set
    3) user does not exists
    """
    # permission_classes = [IsAdminUser]
    permission_classes = [AllowAny]
    @sign_in_pass_document
    def post(self , request):

        mobile = request.data.get("mobile")
        password = request.data.get('password')
        # check if the user mobile or password were entered or not
        if not mobile and not password :
            return ClientErrorResponse.invalid_paramter()

        if not User.user_exist():
            return ClientErrorResponse.not_found(
                en_detail = "Invalid mobile or password" ,
                fa_detail = "شماره یا رمز وارد شده اشتباه است"
            )

        user = User.objects.get_user_with_mobile(mobile=mobile)
        
        if user is not None and user.password is not None:
            if user.check_password(password):
                # create user log
                create_user_log(user , request , kind=0)
                token = create_token(user)
                return ClientOkResponse.ok_with_data(data=token)

            # if password is wrong
            return ClientErrorResponse.not_found(
                en_detail = "Invalid mobile or password" ,
                fa_detail = "شماره یا رمز وارد شده اشتباه است"
            )
        # if user exists but password is not set
        if user is not None and user.password is None :
            return ClientErrorResponse.invalid_paramter(
                en_detail = "Password is not set for the account",
                fa_detail = "رمز عبور برای اکانت تعیین نشده است"
            )

        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR)


# add/update credentials info
class UpdateCredential(APIView) :
    """Update user password"""
    permission_classes = [IsAuthenticated]

    @update_credential_document
    def patch(self , request):
        user = request.user

        serializer = UserPasswordUpdateSerializer(data=request.data , context = {"password" : user.password})
        if not serializer.is_valid():
            ic(serializer.errors)
            return ClientErrorResponse.serializer_error()

        new_password = serializer.validated_data.get("new_password")
        # if something went wrong for the password validation
        if not is_password_valid(new_password):
            return ClientErrorResponse.invalid_paramter(
                fa_detail="پسورد معتبر نمی باشد",
                en_detail="Password is not valid"
            )

        # update user password
        user.set_password(new_password)
        user.save()
        return ClientOkResponse.ok(
            en_detail = "password changed successfully",
            fa_detail = "پسورد با موفقیت تغییر کرد"
        )


class ForgetPassView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request):

        serializer = ForgetPassSerializer(data=request.data)
        if not serializer.is_valid():
            ic(serializer.errors)
            return ClientErrorResponse.serializer_error()

        new_password = serializer.validated_data.get("new_password")
        user_mobile = serializer.validated_data.get("mobile")
        if not is_password_valid(new_password):
            return ClientErrorResponse.invalid_paramter(
                fa_detail="پسورد معتبر نمی باشد",
                en_detail="Invalid password"
            )

        user = User.objects.get_user_with_mobile(user_mobile)
        user.update_password(new_password=new_password)

        return ClientOkResponse.ok(
            fa_detail="پسورد شما با موفقیت آپدیت شد"
        )

