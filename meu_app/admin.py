from django.contrib import admin
from .models import Cliente, Livro, Emprestimo, Reserva


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone", "ativo", "bloqueado")


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "editora", "isbn", "quantidade_disponivel", "quantidade_total", "ativo")


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "livro", "data_retirada", "data_prevista_devolucao", "status")


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("cliente", "livro", "data_reserva", "status")
