# Django & rest
from django.test import TestCase, LiveServerTestCase
from django.db.utils import IntegrityError
from django.urls import reverse
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

from rest_framework.test import APIClient, RequestsClient
from rest_framework_simplejwt.tokens import RefreshToken
# Local
from account.models import User
from account.utils import check_otp

VALID_MOBILE = "09036700953"
INVALID_MOBILE = "911111111111"
SECONDS_VALID_MOBILE = "09198939773"

VALID_PASSWORD = "testpassword1234"
CACHE_KEY = "OTP:{}"

def create_user():
    try:
        return User.objects.create(
            mobile="09036700953",
            password="testpassword1234"
        )
    except IntegrityError:
        return False

def mock_otp(mobile: str = VALID_MOBILE):
    cache.delete(CACHE_KEY.format(mobile))

    valid_otp = "12345"
    hashed_otp = make_password(valid_otp)
    cache.set(CACHE_KEY.format(mobile), hashed_otp)
    return valid_otp

def clear_otp(mobile: str):
    cache.delete(CACHE_KEY.format(mobile))
class UserTestCase(TestCase):
           
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + str(token))

    def test_create_user_with_valid_data(self):
        data = dict(
            mobile="09036700952",
            password="testpassword1234"
        )
        
        new_user = User.objects.create(**data)
        self.assertTrue(new_user, msg="User is not created with valid data")

    def test_create_user_with_invalid_data(self):
        # TODO: Why the user is created with invalid data?
        invalid_data = dict(
            mobile="090367000000953",
            password="testpassword1234"
        )

        with self.assertRaises(ValidationError,  msg="User is created with invalid data"):
            User.objects.create_user(**invalid_data)
    
    def test_avoid_user_creation_with_duplicate_mobile(self):
        self.assertFalse(create_user(), "Duplicate user with mobile has been created")

    def test_login_with_valid_otp(self):
        otp = mock_otp(VALID_MOBILE)
        valid_data = dict(
            mobile=VALID_MOBILE,
            otp=otp
        )
        response = self.client.post(reverse("account:login"), data=valid_data)
        self.assertEqual(response.status_code, 200, msg="User Logged in with valid otp failed")
        clear_otp(VALID_MOBILE)
    
    def test_login_with_invalid_otp(self):
        otp = mock_otp(VALID_MOBILE)
        invalid_data = dict(
            mobile=VALID_MOBILE,
            otp="invalid_otp"
        )
        response = self.client.post(reverse("account:login"), data=invalid_data)
        self.assertEqual(response.status_code, 400, msg="User logged in with invalid otp")
        clear_otp(VALID_MOBILE)

    def test_signup_with_valid_otp(self):

        otp = mock_otp(SECONDS_VALID_MOBILE)
        valid_data = dict(
            mobile=SECONDS_VALID_MOBILE,
            password=VALID_PASSWORD,
            otp=otp
        )
        response = self.client.post(reverse("account:signup"), data=valid_data)
        self.assertEqual(response.status_code, 200, msg="User failed to sign up with valid otp")
        clear_otp(SECONDS_VALID_MOBILE)

    def test_signup_with_invalid_otp(self):
        otp = mock_otp(VALID_MOBILE)
        invalid_data = dict(
            mobile=VALID_MOBILE,
            password=VALID_PASSWORD,
            otp="invalid_otp"
        )
        response = self.client.post(reverse("account:signup"), data=invalid_data)
        self.assertEqual(response.status_code, 400, msg="User Signed up with invalid otp")
        clear_otp(VALID_MOBILE)

    def test_signup_with_invalid_password(self):
        otp = mock_otp(VALID_MOBILE)
        invalid_data = dict(
            mobile=VALID_MOBILE,
            password="invalid",
            otp=otp
        )
        response = self.client.post(reverse("account:signup"), data=invalid_data)
        self.assertEqual(response.status_code, 400, msg="User signed up with invalid passwrod")
        clear_otp(VALID_MOBILE)

    def test_singup_with_invalid_mobile(self):
        otp = mock_otp(INVALID_MOBILE)
        invalid_data = dict(
            mobile=INVALID_MOBILE,
            password=VALID_PASSWORD,
            otp=otp
        )
        response = self.client.post(reverse("account:signup"), data=invalid_data)
        self.assertEqual(response.status_code, 400, msg="User signed up with invalid mobile")
        clear_otp(INVALID_MOBILE)

    def test_update_password_with_valid_data(self):
        update_data = {
            "old_password": self.user.password,
            "new_password": "testnewpassword1234",
            "confirm_password": "testnewpassword1234"
        }
        response = self.client.patch(
            path=reverse("account:update_data"),
            data=update_data
        )

        self.assertEqual(response.status_code, 200, msg="Update password with valid data failed")

    def test_update_password_without_authorization(self):
        update_data = {
            "old_password": "wrong_password",
            "new_password": "testnewpassword1234",
            "confirm_password": "testnewpassword1234"
        }
        # Logout before testing
        self.client.credentials()

        response = self.client.patch(
            path=reverse("account:update_data"),
            data=update_data
        )
        self.assertEqual(response.status_code, 401, msg="User requested to update password without auth")
        self.assertEqual(self.user.password, "testpassword1234", msg="User updated password without auth")

    def test_update_password_with_not_matching_new_and_confirm_password(self):
        update_data = {
            "old_password": self.user.password,
            "new_password": "testnewpassword12345678",
            "confirm_password": "testnewpassword1234"
        }
        response = self.client.patch(
            path=reverse("account:update_data"),
            data=update_data
        )
        self.assertEqual(response.status_code, 400, msg="User updated password with not matching password")

    def test_update_password_with_invalid_old_password(self):
        update_data = {
            "old_password": "wrong_password",
            "new_password": "testnewpassword1234",
            "confirm_password": "testnewpassword1234"
        }
        response = self.client.patch(
            path=reverse("account:update_data"),
            data=update_data
        )
        self.assertEqual(response.status_code, 400, msg="User updated password with invalid old password")

    def test_update_password_with_weak_password(self):
        update_data = {
            "old_password": self.user.password,
            "new_password": "1234",
            "confirm_password": "1234"
        }
        response = self.client.patch(
            path=reverse("account:update_data"),
            data=update_data
        )
        self.assertEqual(response.status_code, 400, msg="User updated password with weak password")

class OtpTestCase(TestCase):
    
    MOBILE = "09036700953"

    def setUp(self):
        self.client = APIClient()
        self.cache_key = CACHE_KEY.format(OtpTestCase.MOBILE)
        self.data = dict(
            mobile=OtpTestCase.MOBILE
        )

    def clear_cache(self):
        cache.delete(self.cache_key)

    def test_get_otp_with_valid_number(self):
        response = self.client.post(reverse("account:send_otp"), data=self.data)
        self.assertEqual(response.status_code, 200)
        self.clear_cache()

    def test_get_otp_with_invalid_number(self):
        invalid_data = dict(
            mobile="0903670095322"
        )
        response = self.client.post(reverse("account:send_otp"), data=invalid_data)
        self.assertEqual(response.status_code, 400)

    def test_duplicate_otp_request(self):
        for _ in range(2):
            response = self.client.post(reverse("account:send_otp"), data=self.data)
        self.assertEqual(response.status_code, 400)
        self.clear_cache()

    def test_validate_otp_with_valid_code(self):

        valid_otp = "12345"
        hashed_otp = make_password(valid_otp)
        cache.set(CACHE_KEY.format(self.MOBILE), hashed_otp)

        self.assertTrue(check_otp(self.MOBILE, otp=valid_otp), msg="Validating otp failed with valid otp")
        self.clear_cache()

    def test_validate_otp_with_invalid_code(self):
        
        response = self.client.post(reverse("account:send_otp"), data=self.data)
        self.assertEqual(response.status_code, 200)

        self.assertFalse(check_otp(self.MOBILE, otp="1234567891"), msg="Validating otp failed with invalid otp")
        self.clear_cache()


# We can use the Live server test case to test on the real server
# The live server will run a local django server instance to run test on that
# We should pass the full url path to the request client
# We can use the live server to test any api not just our api and can be external api too 
class LiveRequestTestCase(LiveServerTestCase):

    def setUp(self):
        self.client = RequestsClient()
        self.user = create_user()
        token = RefreshToken.for_user(self.user).access_token
        self.client.headers["Authorization"] = "Token " + str(token)

    def test_get_otp(self):
        data = dict(
            mobile=VALID_MOBILE
        )
        response = self.client.post(
            self.live_server_url + "/api/v1/account/get-otp/",
            data=data
        )
        self.assertEqual(response.status_code, 200, msg="Live server otp failed")

    def test_update_password(self):
        update_data = {
            "old_password": self.user.password,
            "new_password": "testnewpassword1234",
            "confirm_password": "testnewpassword1234"
        }
        response = self.client.patch(
            url=self.live_server_url + "/api/v1/account/update/",
            data=update_data
        )

        self.assertEqual(response.status_code, 200, msg="Update password with live server failed")
