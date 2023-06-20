"""
URL configuration for disease_detection project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static


from main.views import IndexView
# from dog_eye_detect.views import UploadView, FilesList, IndexView, UploadSuccessView, SelectPredFileView, SelectFileDelView, FileDeleteView


urlpatterns = [
    path('', IndexView.as_view()),
    path('admin/', admin.site.urls),
    path('index/', IndexView.as_view(), name='index'),
    path('dog_skin_detect/', include('dog_skin_detect.urls', namespace='dog_skin_detect')),
                                                        ## include 는 namespace
    path('dog_eye_detect/', include('dog_eye_detect.urls', namespace='dog_eye_detect')),
    path('bulletin/', include('bulletin.urls', namespace='bulletin')),

]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ] + urlpatterns


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


