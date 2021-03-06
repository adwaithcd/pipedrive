"""pipedrive URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path
from lib.records.views import redirectToYellowAntAuthenticationPage,\
    yellowantRedirecturl, yellowantapi, webhook
from lib.web import urls as web_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path("create-new-integration/", redirectToYellowAntAuthenticationPage,
         name="pipedrive-auth-redirect"),
    path("redirecturl/", yellowantRedirecturl, name="yellowant-auth-redirect"),
    path("yellowantauthurl/", redirectToYellowAntAuthenticationPage, name="yellowant-auth-url"),
    path("yellowant-api/", yellowantapi, name="yellowant-api"),
    url('webhook/(?P<hash_str>[^/]+)/$', webhook, name='webhook'),
    path('', include(web_urls)),
]
