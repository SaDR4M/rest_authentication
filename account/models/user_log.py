# django imports
from django.db import models


class UserLog(models.Model):

    user = models.ForeignKey(
        "account.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    ip_address = models.CharField(
        max_length=100,
    )

    browser = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    os = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    device = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    for_admin = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    date = models.DateTimeField(
        auto_now_add=True
    )

    log_kind_choices = (
        (0, "ورود کاربر"),
        (1, "رمز اشتباه"),
        (2, "خروج کاربر"),
        (3, "توکن اشتباه"),
        (4, "در خواست فراموشی رمز عبور با پیامک"),
        (5, "تغییر رمز عبور پس از فراموشی رمز عبور با پیامک"),

    )
    log_kind = models.SmallIntegerField(default=0,
                                        choices=log_kind_choices,
                                        help_text="نوع لاگ",)

    def __str__(self) -> str:
        return self.for_admin
    