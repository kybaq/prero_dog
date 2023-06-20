from django.urls import path,include
from dog_skin_detect.views import IndexView

app_name = 'main'

urlpatterns = [
    path('', IndexView.as_view(), name='IndexView'),
    path('bulletin/', include('bulletin.urls', namespace='bulletin')),
]