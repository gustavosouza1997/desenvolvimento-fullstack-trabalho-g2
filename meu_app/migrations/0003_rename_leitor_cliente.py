from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('meu_app', '0002_livro_ativo'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Leitor',
            new_name='Cliente',
        ),
        migrations.RenameField(
            model_name='emprestimo',
            old_name='leitor',
            new_name='cliente',
        ),
        migrations.RenameField(
            model_name='reserva',
            old_name='leitor',
            new_name='cliente',
        ),
    ]