from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_locationstop_image_locationstop_latitude_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='VenueRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_name', models.CharField(max_length=150)),
                ('contact_name', models.CharField(max_length=120)),
                ('contact_email', models.EmailField(max_length=254)),
                ('contact_phone', models.CharField(blank=True, max_length=40)),
                ('requested_date', models.DateField()),
                ('requested_start_time', models.TimeField(blank=True, null=True)),
                ('requested_end_time', models.TimeField(blank=True, null=True)),
                ('venue_name', models.CharField(max_length=150)),
                ('venue_address', models.CharField(max_length=255)),
                ('estimated_attendance', models.PositiveIntegerField(blank=True, null=True)),
                ('message', models.TextField()),
                ('status', models.CharField(choices=[('new', 'New'), ('in_review', 'In Review'), ('scheduled', 'Scheduled'), ('declined', 'Declined')], default='new', max_length=20)),
                ('staff_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['requested_date', '-created_at'],
            },
        ),
    ]
