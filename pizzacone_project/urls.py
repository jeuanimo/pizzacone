from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

# The custom staff dashboard at /staff/ is the intended way for staff to manage
# the site — regular staff accounts should never need Django admin. This
# restricts /admin/ to superusers only, even if a staff account tries to log
# in there directly.
admin.site.has_permission = lambda request: request.user.is_active and request.user.is_superuser

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('menu/', include('menu.urls')),
    path('staff/', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
else:
    # Render persistent disk stores uploaded media under MEDIA_ROOT.
    # This keeps existing uploaded images visible in production.
    media_url_pattern = r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/')
    urlpatterns += [
        re_path(media_url_pattern, serve, {'document_root': settings.MEDIA_ROOT}),
    ]
