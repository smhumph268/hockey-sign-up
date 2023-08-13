from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


SKILL_LEVEL_CHOICES = (
    ('d', 'D'),
    ('c', 'C'),
    ('b', 'B')
)

PREFERRED_POSITION = (
    ('forward', 'Forward'),
    ('defense', 'Defense'),
    ('goalie', 'Goalie')
)


class CustomUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = models.CharField(unique=True, max_length=30)
    email = models.EmailField(unique=True, max_length=100)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    credits = models.IntegerField(default=0)
    skill_level = models.CharField(max_length=1, choices=SKILL_LEVEL_CHOICES, default='d', help_text='B is the highest level')
    preferred_position = models.CharField(max_length=7, choices=PREFERRED_POSITION, default='forward')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

    def has_credits(self):
        return self.credits > 0
