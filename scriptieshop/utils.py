import sys, os, math
from django.conf import settings
from .models import *

MAX_BIND = 300

def get_variable(variable):
    if variable not in [t[0] for t in Variable.TYPES]:
        raise ValueError('Invalid configuration parameter requested')
    variable, created = Variable.objects.get_or_create(variable=variable)
    return variable

def calculate_cart(prints):
    cart = {
        'prints': [],
        'total': 0,
    }
    total_pages = 0
    total_fc_pages = 0
    total_bw_pages = 0
    total_amount = 0
    total_sheets = 0

    for p in prints:
        p.count_pages()
        total_amount += p.amount
        total_bw_pages += p.bw_pages * p.amount
        total_fc_pages += p.fc_pages * p.amount
        total_pages += p.pages * p.amount
        total_sheets += p.sheets * p.amount

    for p in prints:
        p.price = calculate_price(p, p.amount, total_amount, total_bw_pages, total_fc_pages)
        p.prices = []
        for amount in [1,2,3,4,5,6,7,8,9,10]:
            p.prices.append(calculate_price(p, amount, total_amount, total_bw_pages, total_fc_pages))
        cart['prints'].append(p)
        cart['total'] += p.price['subtotal']

    return cart

def calculate_price(print, amount, total_amount, total_bw_pages, total_fc_pages):
    items = []
    subtotal = 0

    if print.bw_pages:
        x = total_bw_pages - print.amount * print.bw_pages + amount * print.bw_pages
        factor = get_variable(20).value
        a = get_variable(21).value
        b = get_variable(22).value
        c = get_variable(23).value
        d = get_variable(24).value
        price = secret_formula(factor, x, a, b, c, d)
        subsubtotal = amount * print.bw_pages * price
        items.append({
            'amount': amount * print.bw_pages,
            'description': 'Zwart/wit A4 prints',
            'subsubtotal': subsubtotal,
        })
        subtotal += subsubtotal

    if print.fc_pages:
        x = total_fc_pages - print.amount * print.fc_pages + amount * print.fc_pages
        factor = get_variable(30).value
        a = get_variable(31).value
        b = get_variable(32).value
        c = get_variable(33).value
        d = get_variable(34).value
        price = secret_formula(factor, x, a, b, c, d)
        subsubtotal = amount * print.fc_pages * price
        items.append({
            'amount': amount * print.fc_pages,
            'description': 'Kleuren A4 prints',
            'subsubtotal': subsubtotal,
        })
        subtotal += subsubtotal

    if print.papertype == 20:
        price = 0.03
        subsubtotal = amount * print.sheets * price
        items.append({
            'amount': amount * print.sheets,
            'description': print.get_papertype_display() + ' papier',
            'subsubtotal': subsubtotal,
        })
        subtotal += subsubtotal

    if print.papertype == 30:
        price = 0.06
        subsubtotal = amount * print.sheets * price
        items.append({
            'amount': amount * print.sheets,
            'description': print.get_papertype_display() + ' papier',
            'subsubtotal': subsubtotal,
        })
        subtotal += subsubtotal

    if print.sheets > 1 and print.sheets <= MAX_BIND:
        x = print.sheets
        if print.binding == 1:
            a = get_variable(40).value / 100
            b = get_variable(41).value / 10000
        if print.binding == 2:
            a = get_variable(50).value / 100
            b = get_variable(51).value / 10000
        if print.binding == 3:
            a = get_variable(60).value / 100
            b = get_variable(61).value / 10000

        price = bindprice(x, a, b)
        subsubtotal = amount * price
        items.append({
            'amount': amount,
            'description': 'Inbinden met ' + print.get_binding_display().lower(),
            'subsubtotal': subsubtotal,
        })
        subtotal += subsubtotal

        price = 0.5
        subsubtotal = 2 * amount * price
        items.append({
            'amount': 2 * amount,
            'description': 'Inbindcover',
            'subsubtotal': subsubtotal,
        })
        subtotal += subsubtotal
    elif print.sheets > MAX_BIND:
        items.append({})
        items.append({
            'description': '<small>Let op! Dit document heeft teveel pagina’s om in te kunnen binden.</small>',
        })

    return {
        'amount': amount,
        'subtotal': subtotal,
        'perpiece': subtotal / amount,
        'items': items,
    }

def bindprice(x, a, b):
    price = a + b * x
    return round(4*price)/4

def secret_formula(factor, x, a, b, maximum, minimum):

    #### THE SECRET FORMULA: ####
    #                           #
    #            factor         #
    #  price = ---------- + b   #
    #              factor       #
    #      (x-1) + ------       #
    #              a - b        #
    #                           #
    #  a = begin price          #
    #  b = end price            #
    #                           #
    #############################

    # Compensate for the fact that the database stores prices in mils
    factor = factor / 10
    a = a/1000
    b = b/1000
    maximum = maximum/1000
    minimum = minimum/1000

    price = factor / ((x-1) + factor / (a-b)) + b
    price = min(maximum, (max(price, minimum)))
    return price
