from django.urls import path
from account.views import UserOTPApiView , SignInApiView , SignUpApiView, UpdateCredential, ForgetPassView
    
    
# This is namespace for the reverse url patterns match the account then name for the path
app_name = "account"
urlpatterns = [
    path("get-otp/" , UserOTPApiView.as_view() , name="send_otp"),
    path("login/" , SignInApiView.as_view() , name="login"),
    path("signup/" , SignUpApiView.as_view() , name="signup"),
    path("update/", UpdateCredential.as_view(), name="update_data"),
    path("forget-pass/", ForgetPassView.as_view()),
]
