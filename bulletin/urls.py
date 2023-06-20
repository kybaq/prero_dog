from django.urls import path
from bulletin.views import IndexView

app_name = 'bulletin'

urlpatterns = [
    path('', IndexView.as_view(), name='IndexView'),
]