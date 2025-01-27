from django.urls import path
from account.views import UserOTPApiView , SignInApiView , SignUpApiView
    
    
urlpatterns = [
    
    path('get_otp/' , UserOTPApiView.as_view() , name="send_otp"),
    path('signin/' , SignInApiView.as_view() , name="authenticate"),
    path('signup/' , SignUpApiView.as_view() , name="authenticate"),
    
]