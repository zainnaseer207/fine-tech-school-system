from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # include your schoolapp (or app1) urls
    path("", include("schoolapp.urls")),  
]

