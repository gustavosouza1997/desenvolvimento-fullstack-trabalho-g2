from django.urls import path
from django.contrib.auth.views import LoginView
from meu_app import views

urlpatterns = [
    path('', views.index, name='index'),
    path('clientes/', views.listar_clientes, name='listar_clientes'),
    path('cadastrar_cliente/', views.cadastrar_cliente, name='cadastrar_cliente'),
    path('editar_cliente/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('livros/', views.listar_livros, name='listar_livros'),
    path('cadastrar_livro/', views.cadastrar_livro, name='cadastrar_livro'),
    path('editar_livro/<int:id>/', views.editar_livro, name='editar_livro'),
    path('excluir_livro/<int:id>/', views.excluir_livro, name='excluir_livro'),
    path('emprestimos/', views.listar_emprestimos, name='listar_emprestimos'),
    path('devolver_emprestimo/<int:id>/', views.devolver_emprestimo, name='devolver_emprestimo'),
    path('renovar_emprestimo/<int:id>/', views.renovar_emprestimo, name='renovar_emprestimo'),
    path('registrar_ocorrencia/<int:id>/', views.registrar_ocorrencia, name='registrar_ocorrencia'),
    path('reservas/', views.listar_reservas, name='listar_reservas'),
    path('cancelar_reserva/<int:id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('funcionarios/', views.listar_funcionarios, name='listar_funcionarios'),
    path('cadastrar_funcionario/', views.cadastrar_funcionario, name='cadastrar_funcionario'),
    path('editar_funcionario/<int:id>/', views.editar_funcionario, name='editar_funcionario'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.sair, name='logout'),
]
