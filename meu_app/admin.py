from django.contrib import admin
from .models import Usuario, Livro, Emprestimo, Reserva


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone", "ativo", "bloqueado")


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "editora", "isbn", "quantidade_disponivel", "quantidade_total", "ativo")


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "livro", "data_retirada", "data_prevista_devolucao", "status")


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "livro", "data_reserva", "status")
