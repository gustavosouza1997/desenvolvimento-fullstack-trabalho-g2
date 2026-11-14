from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from meu_app.models import Cliente, Emprestimo, Livro, Reserva


class Command(BaseCommand):
    help = 'Completa as coleções de demonstração até 20 registros cada.'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.criar_funcionarios()
            self.criar_clientes()
            self.criar_livros()
            self.criar_emprestimos()
            self.criar_reservas()

        usuario = get_user_model()
        contagens = {
            'funcionários': usuario.objects.filter(is_staff=True).count(),
            'clientes': Cliente.objects.count(),
            'livros': Livro.objects.count(),
            'empréstimos': Emprestimo.objects.count(),
            'reservas': Reserva.objects.count(),
        }
        resumo = ', '.join(nome + ': ' + str(total) for nome, total in contagens.items())
        self.stdout.write(self.style.SUCCESS('Dados de demonstração prontos. ' + resumo))

    def criar_funcionarios(self):
        usuario = get_user_model()
        numero = 1
        while usuario.objects.filter(is_staff=True).count() < 20:
            nome_usuario = 'demo_funcionario_' + str(numero).zfill(2)
            if not usuario.objects.filter(username=nome_usuario).exists():
                funcionario = usuario.objects.create_user(
                    username=nome_usuario,
                    first_name='Funcionário',
                    last_name='Demonstração ' + str(numero).zfill(2),
                    email=nome_usuario + '@example.com',
                    is_staff=True,
                    is_active=True,
                )
                funcionario.set_unusable_password()
                funcionario.save()
            numero += 1

    def criar_clientes(self):
        numero = 1
        while Cliente.objects.count() < 20:
            cpf = '900000000' + str(numero).zfill(2)
            if not Cliente.objects.filter(cpf=cpf).exists():
                Cliente.objects.create(
                    nome='Cliente Demonstração ' + str(numero).zfill(2),
                    cpf=cpf,
                    telefone='1190000' + str(numero).zfill(4),
                    endereco='Rua de Demonstração, ' + str(numero),
                )
            numero += 1

    def criar_livro(self, numero, quantidade_disponivel=1):
        isbn = '9780000000' + str(numero).zfill(3)
        if not Livro.objects.filter(isbn=isbn).exists():
            Livro.objects.create(
                titulo='Livro de Demonstração ' + str(numero).zfill(2),
                autor='Autor de Demonstração ' + str(numero).zfill(2),
                editora='Editora Exemplo',
                ano_publicacao=2005 + numero % 20,
                isbn=isbn,
                genero=['Romance', 'Aventura', 'História', 'Ciência'][numero % 4],
                quantidade_total=1,
                quantidade_disponivel=quantidade_disponivel,
            )

    def criar_livros(self):
        numero = 1
        while Livro.objects.count() < 20:
            self.criar_livro(numero)
            numero += 1

    def criar_emprestimos(self):
        clientes = list(Cliente.objects.filter(ativo=True, bloqueado=False).order_by('id'))
        funcionarios = list(get_user_model().objects.filter(is_staff=True, is_active=True).order_by('id'))
        hoje = timezone.localdate()
        sequencia = Emprestimo.objects.count()
        while Emprestimo.objects.count() < 20:
            livro = Livro.objects.filter(ativo=True, quantidade_disponivel__gt=0).order_by('id').first()
            if livro is None:
                numero = Livro.objects.count() + 1
                self.criar_livro(numero)
                livro = Livro.objects.filter(ativo=True, quantidade_disponivel__gt=0).order_by('id').first()
            sequencia += 1
            cliente = clientes[(sequencia - 1) % len(clientes)]
            Emprestimo.objects.create(
                cliente=cliente,
                livro=livro,
                funcionario=funcionarios[(sequencia - 1) % len(funcionarios)],
                data_retirada=hoje - timedelta(days=sequencia % 12),
                data_prevista_devolucao=hoje + timedelta(days=14),
                status='A',
            )
            Livro.objects.filter(id=livro.id).update(quantidade_disponivel=F('quantidade_disponivel') - 1)

    def criar_reservas(self):
        clientes = list(Cliente.objects.filter(ativo=True, bloqueado=False).order_by('id'))
        funcionarios = list(get_user_model().objects.filter(is_staff=True, is_active=True).order_by('id'))
        sequencia = Reserva.objects.count()
        while Reserva.objects.count() < 20:
            livros_indisponiveis = list(Livro.objects.filter(ativo=True, quantidade_disponivel=0).order_by('id'))
            if not livros_indisponiveis:
                self.criar_livro(Livro.objects.count() + 1, quantidade_disponivel=0)
                livros_indisponiveis = list(Livro.objects.filter(ativo=True, quantidade_disponivel=0).order_by('id'))

            reserva_criada = False
            for livro in livros_indisponiveis:
                for cliente in clientes:
                    if not Reserva.objects.filter(
                        livro=livro,
                        cliente=cliente,
                        status__in=['P', 'D'],
                    ).exists():
                        sequencia += 1
                        Reserva.objects.create(
                            cliente=cliente,
                            livro=livro,
                            funcionario=funcionarios[(sequencia - 1) % len(funcionarios)],
                            status='P',
                        )
                        reserva_criada = True
                        break
                if reserva_criada:
                    break
            if not reserva_criada:
                self.criar_livro(Livro.objects.count() + 1, quantidade_disponivel=0)