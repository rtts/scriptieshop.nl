import os, math

from django.db import models
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.files.storage import FileSystemStorage

from cms.decorators import page_model, section_model
from cms.models import BasePage, BaseSection
from cms.fields import CharField

from .count import count_file

@page_model
class Page(BasePage):
    pass

@section_model
class Section(BaseSection):
    page = models.ForeignKey(Page, related_name='sections', on_delete=models.PROTECT)

class Variable(models.Model):
    TYPES = [
        (10, 'Laag BTW tarief'),
        (11, 'Hoog BTW tarief'),
        (12, 'Verzendkosten'),
        (20, 'Winstfactor zwart/wit'),
        (21, 'Beginprijs zwart/wit'),
        (22, 'Eindprijs zwart/wit'),
        (23, 'Maximummprijs zwart/wit'),
        (24, 'Minimumprijs zwart/wit'),
        (30, 'Winstfactor kleur'),
        (31, 'Beginprijs kleur'),
        (32, 'Eindprijs kleur'),
        (33, 'Maximumprijs kleur'),
        (34, 'Minimumprijs kleur'),
        (40, 'Lijmband basisprijs'),
        (41, 'Lijmband prijs per vel'),
        (50, 'Metalen ring basisprijs'),
        (51, 'Metalen ring prijs per vel'),
        (60, 'Plastic ring basisprijs'),
        (61, 'Plastic ring prijs per vel'),
    ]

    variable = models.PositiveIntegerField('variabele', choices=TYPES, unique=True)
    value = models.PositiveIntegerField('waarde', default=0)

    def __str__(self):
        return str(self.value)

    class Meta:
        verbose_name = 'variabele'
        verbose_name_plural = 'variabelen'
        ordering = ['variable']

ORDER_STATUSES = (
    # These are equal to the statuses that Mollie returns:
    ('open', 'nog niet betaald'),
    ('canceled', 'betaling geannuleerd'),
    ('expired', 'betaling verlopen'),
    ('failed', 'betaling mislukt'),
    ('paid', 'betaald'),
)

class Order(models.Model):
    SHIPPING = (
        (False, 'Afhalen'),
        (True, 'Verzenden'),
    )
    shipping = models.BooleanField('verzendwijze', choices=SHIPPING, default=False)
    customer = CharField('naam')
    email = models.EmailField('e-mail')
    address = models.TextField('adres')
    phone = CharField('telefoonnummer')
    notes = models.TextField('opmerkingen', blank=True)

    total = models.DecimalField('totaalbedrag', max_digits=8, decimal_places=2)
    status = models.CharField('status', max_length=32, choices=ORDER_STATUSES, default=ORDER_STATUSES[0][0])
    created = models.DateTimeField('aangemaakt', auto_now_add=True)
    updated = models.DateTimeField('gewijzigd', auto_now=True)

    assignee = CharField('in behandeling door', blank=True)

    def __str__(self):
        return self.get_order_nr()

    def get_order_nr(self):
        year = self.created.year
        return f'S{year}{self.id:04d}'
    get_order_nr.short_description = 'order nr.'

    def get_description(self):
        return 'Bestelling met nummer ' + self.get_order_nr()

    class Meta:
        ordering = ['-created']
        verbose_name = 'bestelling'
        verbose_name_plural = 'bestellingen'

class Print(models.Model):
    COLOR = (
        (1, 'Automatisch'),
        (2, 'Zwart/Wit'),
    )

    DUPLEX = (
        (False, 'Enkelzijdig'),
        (True, 'Dubbelzijdig'),
    )

    BINDINGS = (
        (1, 'Lijmband'),
        (2, 'Metalen Ring'),
        # (3, 'Plastic Ring'),
    )

    PAPERTYPES = (
        (10, '80 g/m² Navigator'),
        (20, '100 g/m² Color Copy'),
        (30, '120 g/m² Text & Graphics'),
    )

    FRONT_COVERS = (
        (10, 'Transparant mat plastic'),
        (20, 'Transparant glossy plastic'),
        (50, '300 g/m² wit papier met bedrukking'),
    )

    BACK_COVERS = (
        (10, 'Transparant mat plastic'),
        (20, 'Transparant glossy plastic'),
        (30, 'Zwart plastic'),
        (40, 'Wit plastic'),
        (50, '300 g/m² wit papier'),
    )

    order = models.ForeignKey(Order,
                              related_name='prints',
                              blank=True, null=True,
                              on_delete=models.CASCADE)
    safe_storage = FileSystemStorage(location=settings.SAFE_ROOT)
    file = models.FileField('PDF bestand', storage=safe_storage, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    calculated = models.BooleanField(default=False)
    bw_pages = models.PositiveIntegerField('aantal zijdes z/w', default=0)
    fc_pages = models.PositiveIntegerField('aantal zijdes kleur', default=0)
    pages = models.PositiveIntegerField('aantal zijdes', default=0)
    sheets = models.PositiveIntegerField('aantal velletjes', default=0)
    amount = models.PositiveIntegerField('aantal exemplaren', default=1, validators=[MinValueValidator(1)])
    color = models.PositiveIntegerField('kleur', default=1, choices=COLOR)
    duplex = models.BooleanField('duplex', choices=DUPLEX, default=False)
    papertype = models.PositiveIntegerField('papiersoort', choices=PAPERTYPES, default=10)
    front_cover = models.PositiveIntegerField('voorkaft', choices=FRONT_COVERS, default=10)
    back_cover = models.PositiveIntegerField('achterkaft', choices=BACK_COVERS, default=30)
    binding = models.PositiveIntegerField('inbinden', choices=BINDINGS, default=1)
    created = models.DateTimeField('aangemaakt', auto_now_add=True)
    updated = models.DateTimeField('gewijzigd', auto_now=True)

    def __str__(self):
        if self.file:
            return self.original_filename
        return "Scriptie"

    def count_pages(self):
        if self.file and not self.calculated:
            filename = os.path.join(settings.SAFE_ROOT, self.file.name)
            self.bw_pages, self.fc_pages = count_file(filename)
            self.calculated = True

        if self.color == 2:
            self.bw_pages += self.fc_pages
            self.fc_pages = 0

        self.pages = self.bw_pages + self.fc_pages

        if self.duplex:
            self.sheets = math.ceil(self.pages / 2)
        else:
            self.sheets = self.pages

        self.save()
        return self.pages

    class Meta:
        ordering = ['-created']
        verbose_name = 'printopdracht'
        verbose_name_plural = 'printopdrachten'
