from django.urls import path
from account.views import UserOTPApiView , SignInApiView , SignUpApiView, UpdateCredential
    
    
urlpatterns = [
    path("get-otp/" , UserOTPApiView.as_view() , name="send_otp"),
    path("login/" , SignInApiView.as_view() , name="authenticate"),
    path("signup/" , SignUpApiView.as_view() , name="authenticate"),
    path("update/", UpdateCredential.as_view())
]