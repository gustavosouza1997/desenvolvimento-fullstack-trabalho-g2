from django.conf import settings
from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20)
    endereco = models.CharField(max_length=250)
    ativo = models.BooleanField(default=True)
    bloqueado = models.BooleanField(default=False)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        self.nome = self.nome.strip().title()
        self.endereco = self.endereco.strip().title()
        
        super().save(*args, **kwargs)


class Livro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=150)
    editora = models.CharField(max_length=120)
    ano_publicacao = models.PositiveIntegerField()
    isbn = models.CharField(max_length=20, unique=True)
    genero = models.CharField(max_length=100)
    quantidade_total = models.PositiveIntegerField(default=1)
    quantidade_disponivel = models.PositiveIntegerField(default=1)
    capa = models.FileField(upload_to='capas/', blank=True, null=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        self.titulo = self.titulo.strip().title()
        self.autor = self.autor.strip().title()
        self.editora = self.editora.strip().title()
        if self.quantidade_disponivel < 0:
            self.quantidade_disponivel = 0
        super().save(*args, **kwargs)


class Emprestimo(models.Model):
    STATUS_CHOICES = [
        ('A', 'Ativo'),
        ('D', 'Devolvido'),
        ('P', 'Perdido'),
        ('X', 'Danificado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='emprestimos')
    livro = models.ForeignKey(Livro, on_delete=models.PROTECT, related_name='emprestimos')
    funcionario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    data_retirada = models.DateField(default=timezone.localdate)
    data_prevista_devolucao = models.DateField()
    data_devolucao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    observacao = models.TextField(blank=True)

    def __str__(self):
        return f'{self.livro.titulo} - {self.cliente.nome}'


class Reserva(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pendente'),
        ('D', 'Disponível para retirada'),
        ('A', 'Atendida'),
        ('C', 'Cancelada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='reservas')
    livro = models.ForeignKey(Livro, on_delete=models.PROTECT, related_name='reservas')
    funcionario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    data_reserva = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')

    def __str__(self):
        return f'{self.livro.titulo} - {self.cliente.nome}'

