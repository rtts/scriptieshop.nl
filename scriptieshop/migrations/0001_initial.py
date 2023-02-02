import cms.fields
import cms.mixins
import django.core.files.storage
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import embed_video.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shipping', models.BooleanField(choices=[(False, 'Afhalen'), (True, 'Verzenden')], default=False, verbose_name='verzendwijze')),
                ('customer', cms.fields.CharField()),
                ('email', models.EmailField(max_length=254, verbose_name='e-mail')),
                ('address', models.TextField(verbose_name='adres')),
                ('phone', cms.fields.CharField()),
                ('notes', models.TextField(blank=True, verbose_name='opmerkingen')),
                ('total', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='totaalbedrag')),
                ('status', models.CharField(choices=[('open', 'nog niet betaald'), ('canceled', 'betaling geannuleerd'), ('expired', 'betaling verlopen'), ('failed', 'betaling mislukt'), ('paid', 'betaald')], default='open', max_length=32, verbose_name='status')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='aangemaakt')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='gewijzigd')),
                ('assignee', cms.fields.CharField()),
            ],
            options={
                'verbose_name': 'bestelling',
                'verbose_name_plural': 'bestellingen',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', cms.fields.CharField()),
                ('slug', cms.fields.SlugField(unique=True)),
                ('number', cms.fields.PositiveIntegerField()),
                ('menu', cms.fields.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'page',
                'verbose_name_plural': 'pages',
                'ordering': ['number'],
                'abstract': False,
            },
            bases=(cms.mixins.Numbered, models.Model),
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variable', models.PositiveIntegerField(choices=[(10, 'Laag BTW tarief'), (11, 'Hoog BTW tarief'), (12, 'Verzendkosten'), (20, 'Winstfactor zwart/wit'), (21, 'Beginprijs zwart/wit'), (22, 'Eindprijs zwart/wit'), (23, 'Maximummprijs zwart/wit'), (24, 'Minimumprijs zwart/wit'), (30, 'Winstfactor kleur'), (31, 'Beginprijs kleur'), (32, 'Eindprijs kleur'), (33, 'Maximumprijs kleur'), (34, 'Minimumprijs kleur'), (40, 'Lijmband basisprijs'), (41, 'Lijmband prijs per vel'), (50, 'Metalen ring basisprijs'), (51, 'Metalen ring prijs per vel'), (60, 'Plastic ring basisprijs'), (61, 'Plastic ring prijs per vel')], unique=True, verbose_name='variabele')),
                ('value', models.PositiveIntegerField(default=0, verbose_name='waarde')),
            ],
            options={
                'verbose_name': 'variabele',
                'verbose_name_plural': 'variabelen',
                'ordering': ['variable'],
            },
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', cms.fields.CharField()),
                ('type', cms.fields.CharField()),
                ('number', cms.fields.PositiveIntegerField()),
                ('content', cms.fields.TextField()),
                ('image', cms.fields.ImageField()),
                ('video', embed_video.fields.EmbedVideoField(blank=True, help_text='Paste a YouTube, Vimeo, or SoundCloud link', verbose_name='video')),
                ('href', cms.fields.CharField()),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sections', to='scriptieshop.page')),
            ],
            options={
                'verbose_name': 'section',
                'verbose_name_plural': 'sections',
                'ordering': ['number'],
                'abstract': False,
            },
            bases=(cms.mixins.Numbered, models.Model),
        ),
        migrations.CreateModel(
            name='Print',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, storage=django.core.files.storage.FileSystemStorage(location='/srv/scriptieshop/customer_files'), upload_to='', verbose_name='PDF bestand')),
                ('original_filename', models.CharField(blank=True, max_length=255)),
                ('calculated', models.BooleanField(default=False)),
                ('bw_pages', models.PositiveIntegerField(default=0, verbose_name='aantal zijdes z/w')),
                ('fc_pages', models.PositiveIntegerField(default=0, verbose_name='aantal zijdes kleur')),
                ('pages', models.PositiveIntegerField(default=0, verbose_name='aantal zijdes')),
                ('sheets', models.PositiveIntegerField(default=0, verbose_name='aantal velletjes')),
                ('amount', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='aantal exemplaren')),
                ('color', models.PositiveIntegerField(choices=[(1, 'Automatisch'), (2, 'Zwart/Wit')], default=1, verbose_name='kleur')),
                ('duplex', models.BooleanField(choices=[(False, 'Enkelzijdig'), (True, 'Dubbelzijdig')], default=False, verbose_name='duplex')),
                ('papertype', models.PositiveIntegerField(choices=[(10, '80 g/m² Navigator'), (20, '100 g/m² Color Copy'), (30, '120 g/m² Text & Graphics')], default=10, verbose_name='papiersoort')),
                ('front_cover', models.PositiveIntegerField(choices=[(10, 'Transparant mat plastic'), (20, 'Transparant glossy plastic'), (50, '300 g/m² wit papier met bedrukking')], default=10, verbose_name='voorkaft')),
                ('back_cover', models.PositiveIntegerField(choices=[(10, 'Transparant mat plastic'), (20, 'Transparant glossy plastic'), (30, 'Zwart plastic'), (40, 'Wit plastic'), (50, '300 g/m² wit papier')], default=30, verbose_name='achterkaft')),
                ('binding', models.PositiveIntegerField(choices=[(1, 'Lijmband'), (2, 'Metalen Ring')], default=1, verbose_name='inbinden')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='aangemaakt')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='gewijzigd')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prints', to='scriptieshop.order')),
            ],
            options={
                'verbose_name': 'printopdracht',
                'verbose_name_plural': 'printopdrachten',
                'ordering': ['-created'],
            },
        ),
    ]
