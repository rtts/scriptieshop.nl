from django import forms

from .utils import calculate_cart, get_variable
from .models import *

class PriceCurveForm(forms.Form):
    factor = forms.IntegerField(label='Winstfactor', min_value=1)
    begin = forms.IntegerField(label='Beginprijs', min_value=0)
    end = forms.IntegerField(label='Eindprijs', min_value=0)
    maximum = forms.IntegerField(label='Mininum', min_value=0)
    minimum = forms.IntegerField(label='Mininum', min_value=0)
    vat = forms.IntegerField(label='Laag BTW tarief', min_value=0)

    def save(self, variables):
        for variable in variables:
            variables[variable].value = self.cleaned_data[variable]
            variables[variable].save()

class BindPriceForm(forms.Form):
    glue1 = forms.IntegerField(label='Lijmband basisprijs', min_value=0)
    glue2 = forms.IntegerField(label='Lijmband meerprijs per vel', min_value=0)
    metal1 = forms.IntegerField(label='Metalen ring basisprijs', min_value=0)
    metal2 = forms.IntegerField(label='Metalen ring meerprijs per vel', min_value=0)
    plastic1 = forms.IntegerField(label='Plastic ring basisprijs', min_value=0)
    plastic2 = forms.IntegerField(label='Plastic ring meerprijs per vel', min_value=0)
    vat = forms.IntegerField(label='Laag BTW tarief', min_value=0)

    def save(self, variables):
        for variable in variables:
            variables[variable].value = self.cleaned_data[variable]
            variables[variable].save()

class PrintForm(forms.ModelForm):
    def save(self):
        p = super().save(commit=False)
        file = self.cleaned_data.get('file')

        # Heads up: the following still doesn't work for re-uploads
        if file and not p.original_filename:
            p.original_filename = file.name
            p.calculated = False
            p.save()

            # If it's an invalid PDF
            if not p.count_pages():
                p.file = None
                p.save()

        p.save()
        return p

    class Meta:
        model = Print
        fields = ['bw_pages', 'fc_pages', 'file', 'duplex', 'papertype', 'binding', 'front_cover', 'back_cover']

class UploadForm(PrintForm):
    def clean(self):
        cleaned_data = super().clean()
        if self.files or cleaned_data['bw_pages'] or cleaned_data['fc_pages']:
            return cleaned_data
        else:
            raise forms.ValidationError('Oeps! Geef het aantal zijdes op óf upload een PDF bestand!')

class CartItemForm(PrintForm):
    amount = forms.ChoiceField(label='Aantal')

    class Meta:
        model = Print
        fields = ['file', 'amount', 'duplex', 'papertype', 'binding', 'front_cover', 'back_cover']

class CartForm(UploadForm):
    def __init__(self, prints, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''

        self.formset = forms.modelformset_factory(
            model = Print,
            form = CartItemForm,
            extra=0,
        )(
            queryset = prints,
            data=self.data if self.is_bound else None,
            files=self.files if self.is_bound else None,
            form_kwargs={'label_suffix': self.label_suffix},
        )

        cart = calculate_cart(prints)

        for print, form in zip(cart['prints'], self.formset):
            choices = []
            print.price = print.prices[print.amount-1]
            form.print = print
            for p in print.prices:
                amount = p['amount']
                description = f"{amount} voor €{p['perpiece']:.2f} per stuk"
                choices.append((amount, description))
            form.fields['amount'].choices = choices

        self.total = cart['total']

    def is_valid(self):
        return super().is_valid() and self.formset.is_valid()

    def clean(self):
        if self.has_changed():
            super().clean()
        if not self.formset.is_valid():
            self.add_error(None, 'Oeps')

    def save(self):
        if self.has_changed():
            super().save()
        for form in self.formset:
            form.save()
        return self.instance

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['shipping', 'customer', 'email', 'address', 'phone', 'notes']

    def __init__(self, prints, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prints = prints
        self.label_suffix = ''

    def save(self):
        order = super().save(commit=False)
        cart = calculate_cart(self.prints)
        order.total = cart['total']
        if order.shipping:
            order.total += get_variable(12).value / 100
        order.save()
        for p in self.prints:
            p.order = order
            p.save()
        return order
