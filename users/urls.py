from django.urls import path,include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('user', UserAPIView, basename='User')
router.register('login',LoginAPIView,basename='Login')
router.register('secret-key',SecretKeyValidationAPI,basename="Secret Key")
router.register('forgot-password',ResetPasswordAPIView,basename='ForgotPassword')
router.register('reset-link-validate',ValidateResetLink,basename='ResetLinkValidate')
router.register('system-info', SystemInfoViewSet, basename='system-info')
router.register('serial-number-validate', SerialNumberValidationViewSet, basename='SerialNumberValidationAPI')
router.register('role',RoleViewSet,basename="RoleAPIView")
router.register('mac-address-update', MacAddressUpdateViewSet, basename="MacAddressUpdateAPIView")

urlpatterns= [
    path('', include(router.urls)),
]