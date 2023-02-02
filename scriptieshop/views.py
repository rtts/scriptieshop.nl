import logging

from django.conf import settings
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.shortcuts import redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, DetailView
from django.core.exceptions import SuspiciousOperation
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.decorators.http import require_http_methods

from mollie.api.client import Client
from cms.forms import ContactForm
from cms.decorators import section_view
from cms.views import SectionView, SectionFormView

from .utils import *
from .models import *
from .forms import *

logger = logging.getLogger('django.request')
mollie_client = Client()
mollie_client.set_api_key(settings.MOLLIE_API_KEY)

@csrf_exempt
@require_http_methods(['POST'])
def webhook(request):
    try:
        payment_id = request.POST.get('id')
        payment = mollie_client.payments.get(payment_id)
        order_id = payment.metadata['order_id']
        order = Order.objects.get(id=order_id)
        if order.status == payment.status or order.status == 'paid':
            raise SuspiciousOperation(
                f'Something weird happened:'
                f'Mollie called the webhook with status = "{payment.status}"'
                f'but the order status is already "{order.status}"')
        order.status = payment.status
        order.save()
        if order.status == 'paid':
            send_email(order)

    except Exception:
        import traceback
        logger.error(traceback.format_exc())

    # Always return successfully, as to not leak information
    return HttpResponse()

def get_payment_url(order):
    amount = {
        'currency': 'EUR',
        'value': f'{order.total:.2f}',
        }
    description = order.get_description()
    webhookUrl = settings.CANONICAL_URL + reverse('webhook')
    redirectUrl = settings.CANONICAL_URL + '/betaald/'
    metadata = {'order_id': str(order.id)}
    payment = mollie_client.payments.create({
        'amount': amount,
        'description': description,
        'webhookUrl': webhookUrl,
        'redirectUrl': redirectUrl,
        'metadata': metadata,
    })
    return payment.checkout_url

def send_email(order):
    body = f'''Beste Copyshoppers,

Iemand heeft een opdracht geplaatst op Scriptieshop.nl. De betaling
met iDeal is geslaagd. Dat betekent dat we nu zo snel mogelijk aan de
slag moeten om deze bestelling te printen en te versturen!

Je kunt de details van deze bestelling bekijken op de opdrachtbon:
https://www.scriptieshop.nl/opdracht/{order.pk}/
Hier kun je ook de benodigde bestanden downloaden.

Als je contact op wilt nemen met de besteller kan dat door simpelweg
op deze email te antwoorden. Het Reply-To adres is ingesteld op
{order.email}.

Vergeet niet deze tekst te verwijderen uit je antwoord :-)

Groeten,
De server op Scriptieshop.nl
'''
    email = EmailMessage(
        to=settings.DEFAULT_TO_EMAIL,
        from_email=settings.DEFAULT_FROM_EMAIL,
        body=body,
        subject=order.get_description(),
        headers={'Reply-To': order.email},
    )
    email.send()

@section_view
class Text(SectionView):
    verbose_name = 'Tekst'
    fields = ['content']
    template_name = 'text.html'

@section_view
class Image(SectionView):
    verbose_name = 'Afbeelding'
    fields = ['image']
    template_name = 'image.html'

@section_view
class Steps(SectionView):
    verbose_name = 'Stappenplan'
    fields = ['content']
    template_name = 'steps.html'

@section_view
class Upload(SectionFormView):
    verbose_name = 'Upload'
    fields = ['title']
    template_name = 'upload.html'
    form_class = UploadForm

    def form_valid(self, form):
        p = form.save()
        pks = self.request.session.get('pks', [])
        if p.pk not in pks:
            pks.append(p.pk)
        self.request.session['pks'] = pks
        return redirect('/cart/')

@section_view
class Cart(SectionFormView):
    verbose_name = 'Winkelwagentje'
    fields = ['content', 'href']
    template_name = 'cart.html'
    form_class = CartForm

    def get_form_kwargs(self):
        pks = self.request.session.get('pks', [])
        self.prints = Print.objects.filter(pk__in=pks)
        return {'prints': self.prints}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invalid'] = not self.prints or not all([p.file for p in self.prints])
        context['vat'] = get_variable(10).value
        return context

    def form_valid(self, form):
        pks = self.request.session.get('pks', [])
        p = form.save()
        if p.pk not in pks:
            pks.append(p.pk)
        self.request.session['pks'] = pks
        return redirect('/cart/')

@section_view
class Checkout(SectionFormView):
    verbose_name = 'Bestellen'
    fields = ['content']
    template_name = 'checkout.html'
    form_class = CheckoutForm

    def get_form_kwargs(self):
        pks = self.request.session.get('pks', [])
        self.prints = Print.objects.filter(pk__in=pks)
        return {'prints': self.prints}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pks = self.request.session.get('pks', [])
        context['shipping_costs'] = get_variable(12).value / 100
        context['prints'] = Print.objects.filter(pk__in=pks).exclude(file='')
        context['cart'] = calculate_cart(context['prints'])
        return context

    def form_valid(self, form):
        order = form.save()
        self.request.session['pks'] = []
        if settings.DEBUG:
            send_email(order)
            return redirect('/betaald/')
        if order.status == 'paid':
            return redirect('/betaald/')
        payment_url = get_payment_url(order)
        return redirect(payment_url)

@section_view
class Contact(SectionFormView):
    verbose_name = 'Contact'
    fields = []
    template_name = 'contact.html'
    form_class = ContactForm
    success_url = '/thanks/'


###############################################################################


class Worksheet(UserPassesTestMixin, DetailView):
    template_name = 'worksheet.html'
    model = Order

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prints'] = self.object.prints.all()
        return context

class BindPrice(UserPassesTestMixin, FormView):
    form_class = BindPriceForm
    template_name = 'bindprice.html'

    def test_func(self):
        return self.request.user.has_perm('shop_variable_change')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'initial': self.get_variables()})
        return kwargs

    def get_variables(self):
        return {
            'glue1': get_variable(40),
            'glue2': get_variable(41),
            'metal1': get_variable(50),
            'metal2': get_variable(51),
            'plastic1': get_variable(60),
            'plastic2': get_variable(61),
            'vat': get_variable(10),
        }

    def form_valid(self, form):
        form.save(self.get_variables())
        return redirect('/cart/')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_variables())
        return context

class PriceCurve(UserPassesTestMixin, FormView):
    form_class = PriceCurveForm
    template_name = 'pricecurve.html'

    def test_func(self):
        return self.request.user.has_perm('shop_variable_change')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'initial': self.get_variables()})
        return kwargs

    def form_valid(self, form):
        form.save(self.get_variables())
        return redirect('/cart/')

class BWPriceCurve(PriceCurve):
    def get_variables(self):
        return {
            'factor': get_variable(20),
            'begin': get_variable(21),
            'end': get_variable(22),
            'maximum': get_variable(23),
            'minimum': get_variable(24),
            'vat': get_variable(10),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_variables())
        context['include_legacy_bw'] = True
        return context

class ColorPriceCurve(PriceCurve):
    def get_variables(self):
        return {
            'factor': get_variable(30),
            'begin': get_variable(31),
            'end': get_variable(32),
            'maximum': get_variable(33),
            'minimum': get_variable(34),
            'vat': get_variable(10),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_variables())
        context['include_legacy_fc'] = True
        return context
