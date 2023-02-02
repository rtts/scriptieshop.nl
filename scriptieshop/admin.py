from django.contrib import admin
from django.urls import reverse
from django.utils.html import mark_safe

from .models import *

@admin.register(Variable)
class VariableAdmin(admin.ModelAdmin):
    list_display = ['get_variable_display', 'value']
    exclude = ['variable']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['get_order_nr', 'created', 'customer', 'total', 'status', 'get_shipping_display', 'get_worksheet']
    list_filter = ['status', 'created', 'customer']
    readonly_fields = ['total', 'status']

    def get_worksheet(self, order):
        url = reverse('worksheet', args=[order.pk])
        return mark_safe(f'<a style="font-size:1.25em" href="{url}">Bekijk opdrachtbon</a>')
    get_worksheet.short_description = 'opdrachtbon'
