from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager as DjangoBaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import (
    RegexValidator
)


class BaseUserManager(DjangoBaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, phone, password, **extra_fields):
        """Create and save a User with the given phone and password."""
        if not phone:
            raise ValueError("The given phone must be set")

        user = self.model(phone=phone, **extra_fields)

        if password is None:
            raise ValueError("The password must be set")
        
        user.set_password(password)

        user.save(using=self._db)
        return user

    def create(self, phone, password, **extra_fields):
        """Create and save a regular User with the given phone and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra_fields)

    def create_staffuser(self, phone, password=None, **extra_fields):
        """Create and save a staff User with the given phone and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password=None, **extra_fields):
        """Create and save a SuperUser with the given phone and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone, password, **extra_fields)

class User(AbstractUser):
    objects = BaseUserManager()
    username = None
    name = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, validators=[RegexValidator(regex=r'^\+{1}?\d{9,15}$')], unique=True)
        
    is_active = models.BooleanField(default=True, null=True)
    inactive_player = models.BooleanField(default=False)
    lastTimeInSystem = models.DateTimeField(default=timezone.now)
    timezone = models.CharField(max_length=200, null=False, db_index=True, default='America/Havana')


    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["password"]
    
    class Meta:
        db_table = 'user'

        
    @property
    def is_block(self):
        from tu_entrega_app.models import BlockPlayer
        return BlockPlayer.objects.filter(player_blocked__id = self.id).exists()
    

    def __str__(self):
        return f"{self.name}" if self.name else f"{self.phone}"
    
    class Meta:
        ordering = ['-date_joined']