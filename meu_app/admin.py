from django.contrib import admin
from .models import Cliente, Emprestimo, Livro, Reserva


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone", "ativo", "bloqueado")


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "editora", "ano_publicacao", "quantidade_disponivel", "ativo")


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "livro", "funcionario", "data_retirada", "status")


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("cliente", "livro", "funcionario", "data_reserva", "status")
