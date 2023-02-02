from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.urls import path, re_path, include
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .models import Order
from .views import *

admin.site.site_header = settings.PROJECT_NAME.capitalize()
admin.site.site_title = settings.PROJECT_NAME.capitalize()
admin.site.enable_nav_sidebar = False

def forget(request, pk):
    pks = request.session.get('pks', [])
    if int(pk) in pks:
        pks.remove(int(pk))
        request.session['pks'] = pks
    return redirect('/cart/')

def topsecret(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    filename = request.path.split('/')[-1]
    response = HttpResponse()
    response['Content-Type'] = ''
    response['X-Accel-Redirect'] = f'/topsecret/{filename}' # nginx internal location
    return response

urlpatterns = staticfiles_urlpatterns() + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', RedirectView.as_view(url='/accounts/login/')),
    path('logout/', RedirectView.as_view(url='/accounts/logout/')),
    path('bindprice/', BindPrice.as_view(), name='bindprice'),
    path('bwprice/', BWPriceCurve.as_view(), name='bwprice'),
    path('fcprice/', ColorPriceCurve.as_view(), name='fcprice'),
    path('opdracht/<int:pk>/', Worksheet.as_view(), name='worksheet'),
    path('cancel/<int:pk>/', forget, name='forget'),
    re_path('download/', topsecret, name='download'),
    path('mollie-webhook/', webhook, name='webhook'),
    path('', include('cms.urls', namespace='cms')),
]
