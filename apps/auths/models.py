from typing import ClassVar

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, PermissionsMixin, UserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(
            self,
            email: str,
            password: str | None = None,
            **extra_fields,
                     ):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email).lower()

        user = self.model(email=email, **extra_fields),
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
            self,
            email: str,
            password: str | None = None,
            **extra_fields,
    ):
        extra_fields.setdefault('is_staff', True),
        extra_fields.setdefault('is_superuser', True),
        extra_fields.setdefault('is_active', True),

        return self.create_user(email, password, **extra_fields)

    class User(AbstractUser, PermissionsMixin):
        email = models.EmailField(unique=True)
        first_name = models.CharField(max_length=50)
        last_name = models.CharField(max_length=50)
        is_active = models.BooleanField(default=True)
        is_staff = models.BooleanField(default=False)

        objects = UserManager()

        USERNAME_FIELD = 'email'
        REQUIRED_FIELDS :ClassVar[list[str]] =  ['first_name', 'last_name']

        def __str__(self):
            return self.email