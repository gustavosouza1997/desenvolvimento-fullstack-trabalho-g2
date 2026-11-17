from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('meu_app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(old_name='Cliente', new_name='Usuario'),
        migrations.RenameField(model_name='emprestimo', old_name='cliente', new_name='usuario'),
        migrations.RenameField(model_name='reserva', old_name='cliente', new_name='usuario'),
    ]
