from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Q, Count
from django.db.models.functions import Lower
from django.utils import timezone

from .models import Cliente, Livro, Emprestimo, Reserva
from .forms import (
    ClienteForm,
    LivroForm,
    EmprestimoForm,
    ReservaForm,
    RenovacaoForm,
    OcorrenciaForm,
    FuncionarioForm,
    EditarFuncionarioForm,
    RelatorioForm,
)


@login_required
def index(request):

    dados = {
        'total_livros': Livro.objects.filter(ativo=True).count(),
        'total_clientes': Cliente.objects.filter(ativo=True).count(),
        'emprestimos_ativos': Emprestimo.objects.filter(status='A').count(),
        'emprestimos_atrasados': Emprestimo.objects.filter(
            status='A',
            data_prevista_devolucao__lt=timezone.localdate()
        ).count(),
        'reservas_para_retirada': Reserva.objects.filter(status='D').select_related('cliente', 'livro'),
    }

    return render(request, 'index.html', dados)


def sair(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    else:
        return redirect('index')


class AlterarSenhaView(PasswordChangeView):
    template_name = 'alterar_senha.html'
    success_url = '/'

    def form_valid(self, form):
        messages.success(self.request, 'Senha alterada com sucesso!')
        return super().form_valid(form)


@login_required
def listar_funcionarios(request):

    if not request.user.is_superuser:
        messages.error(
            request, 'Acesso permitido somente para administradores.')
        return redirect('index')

    ordem = request.GET.get('ordem')
    nome_da_pesquisa = request.GET.get('nome_da_pesquisa', '')

    funcionarios = User.objects.filter(
        Q(first_name__icontains=nome_da_pesquisa) | Q(
            username__icontains=nome_da_pesquisa),
        is_staff=True,
        is_active=True,
    ).order_by(Lower('first_name'))

    if ordem == 'decrescente':
        funcionarios = funcionarios.order_by(Lower('first_name').desc())

    dados = {
        'funcionarios': funcionarios,
        'nome_da_pesquisa': nome_da_pesquisa,
    }

    return render(request, 'listar_funcionarios.html', dados)


@login_required
def cadastrar_funcionario(request):

    if not request.user.is_superuser:
        messages.error(
            request, 'Acesso permitido somente para administradores.')
        return redirect('index')

    if request.method == 'POST':
        form = FuncionarioForm(request.POST)

        if form.is_valid():
            funcionario = form.save(commit=False)
            funcionario.is_staff = True
            funcionario.save()

            usuario = form.cleaned_data['username']
            mensagem_confirmacao = f'Funcionário {usuario} cadastrado com sucesso!'
            messages.success(request, mensagem_confirmacao)

            return redirect('listar_funcionarios')
    else:
        form = FuncionarioForm()

    dados = {
        'formulario': form
    }

    return render(request, 'cadastrar_funcionario.html', dados)


@login_required
def editar_funcionario(request, id):

    if not request.user.is_superuser:
        messages.error(
            request, 'Acesso permitido somente para administradores.')
        return redirect('index')

    funcionario = User.objects.get(id=id, is_staff=True)

    form = EditarFuncionarioForm(instance=funcionario)

    if request.method == 'POST':

        form = EditarFuncionarioForm(request.POST, instance=funcionario)

        if form.is_valid():
            form.save()
            usuario = form.cleaned_data['username']

            mensagem_confirmacao = f'Funcionário {usuario} alterado com sucesso!'
            messages.success(request, mensagem_confirmacao)

            return redirect('listar_funcionarios')

    dados = {
        'formulario': form
    }

    return render(request, 'editar_funcionario.html', dados)


@login_required
def desativar_funcionario(request, id):

    if not request.user.is_superuser:
        messages.error(
            request, 'Acesso permitido somente para administradores.')
        return redirect('index')

    funcionario = User.objects.get(id=id, is_staff=True)

    if funcionario == request.user:
        messages.error(request, 'Você não pode desativar a sua própria conta.')
        return redirect('listar_funcionarios')

    if request.method == 'POST':
        funcionario.is_active = False
        funcionario.save()

        mensagem = f'Funcionário {funcionario.username} desativado com sucesso'
        messages.success(request, mensagem)

    return redirect('listar_funcionarios')


@login_required
def funcionarios_inativos(request):

    if not request.user.is_superuser:
        messages.error(
            request, 'Acesso permitido somente para administradores.')
        return redirect('index')

    funcionarios = User.objects.filter(
        is_staff=True,
        is_active=False
    ).order_by(Lower('first_name'))

    dados = {
        'funcionarios': funcionarios
    }

    return render(request, 'funcionarios_inativos.html', dados)


@login_required
def ativar_funcionario(request, id):

    if not request.user.is_superuser:
        messages.error(
            request, 'Acesso permitido somente para administradores.')
        return redirect('index')

    funcionario = User.objects.get(id=id, is_staff=True)

    if request.method == 'POST':
        funcionario.is_active = True
        funcionario.save()

        mensagem = f'Funcionário {funcionario.username} ativado com sucesso'
        messages.success(request, mensagem)

    return redirect('funcionarios_inativos')


@login_required
def listar_clientes(request):

    ordem = request.GET.get('ordem')
    nome_da_pesquisa = request.GET.get('nome_da_pesquisa', '')

    clientes = Cliente.objects.filter(
        Q(nome__icontains=nome_da_pesquisa) | Q(
            cpf__icontains=nome_da_pesquisa),
        ativo=True,
    ).order_by(Lower('nome'))

    if ordem == 'decrescente':
        clientes = clientes.order_by(Lower('nome').desc())

    dados = {
        'clientes': clientes,
        'nome_da_pesquisa': nome_da_pesquisa,
    }

    return render(request, 'listar_clientes.html', dados)


@login_required
def cadastrar_cliente(request):

    if request.method == 'POST':
        form = ClienteForm(request.POST)

        if form.is_valid():
            form.save()
            nome = form.cleaned_data['nome']

            mensagem_confirmacao = f'Cliente {nome} cadastrado com sucesso!'
            messages.success(request, mensagem_confirmacao)

            return redirect('listar_clientes')
    else:
        form = ClienteForm()

    dados = {
        'formulario': form
    }

    return render(request, 'cadastrar_cliente.html', dados)


@login_required
def editar_cliente(request, id):

    cliente = Cliente.objects.get(id=id)

    form = ClienteForm(instance=cliente)

    if request.method == 'POST':

        form = ClienteForm(request.POST, instance=cliente)

        if form.is_valid():
            form.save()
            nome = form.cleaned_data['nome']

            mensagem_confirmacao = f'Cliente {nome} alterado com sucesso!'
            messages.success(request, mensagem_confirmacao)

            return redirect('listar_clientes')

    dados = {
        'formulario': form,
        'cliente': cliente,
    }

    return render(request, 'editar_cliente.html', dados)


@login_required
def desativar_cliente(request, id):

    cliente = Cliente.objects.get(id=id)

    if request.method == 'POST':
        # Não pode desativar quem ainda está com livro ou na fila de reservas
        emprestimos_ativos = cliente.emprestimos.filter(status='A').count()
        reservas_ativas = cliente.reservas.filter(status__in=['P', 'D']).count()

        if emprestimos_ativos:
            messages.error(request, f'{cliente.nome} ainda tem {emprestimos_ativos} empréstimo(s) ativo(s). Registre a devolução antes de desativar.')
            return redirect('editar_cliente', id=cliente.id)

        if reservas_ativas:
            messages.error(request, f'{cliente.nome} tem {reservas_ativas} reserva(s) ativa(s). Cancele as reservas antes de desativar.')
            return redirect('editar_cliente', id=cliente.id)

        cliente.ativo = False
        cliente.save()

        messages.success(request, f'Cliente {cliente.nome} desativado com sucesso')

    return redirect('listar_clientes')


@login_required
def clientes_inativos(request):

    clientes = Cliente.objects.filter(ativo=False).order_by(Lower('nome'))

    dados = {
        'clientes': clientes
    }

    return render(request, 'clientes_inativos.html', dados)


@login_required
def ativar_cliente(request, id):

    cliente = Cliente.objects.get(id=id)

    if request.method == 'POST':
        cliente.ativo = True
        cliente.save()

        messages.success(request, f'Cliente {cliente.nome} ativado com sucesso')

    return redirect('clientes_inativos')


@login_required
def desbloquear_cliente(request, id):

    cliente = Cliente.objects.get(id=id)

    if request.method == 'POST':
        cliente.bloqueado = False
        cliente.save()

        mensagem = f'Cliente {cliente.nome} desbloqueado com sucesso'
        messages.success(request, mensagem)

    return redirect('listar_clientes')


@login_required
def listar_livros(request):

    ordem = request.GET.get('ordem', 'titulo')
    pesquisa = request.GET.get('pesquisa', '')
    disponiveis = request.GET.get('disponiveis', '')

    livros = Livro.objects.filter(
        Q(titulo__icontains=pesquisa) |
        Q(autor__icontains=pesquisa) |
        Q(genero__icontains=pesquisa) |
        Q(isbn__icontains=pesquisa),
        ativo=True,
    )

    if disponiveis == 'sim':
        livros = livros.filter(quantidade_disponivel__gt=0)

    if ordem not in ['titulo', '-titulo', 'autor', '-autor']:
        ordem = 'titulo'

    campo = Lower(ordem.lstrip('-'))
    campo = campo.desc() if ordem.startswith('-') else campo.asc()

    livros = livros.order_by(campo, Lower('titulo'))

    dados = {
        'livros': livros,
        'pesquisa': pesquisa,
        'disponiveis': disponiveis,
        'ordem': ordem,
    }

    return render(request, 'listar_livros.html', dados)


@login_required
def cadastrar_livro(request):

    if request.method == 'POST':
        form = LivroForm(request.POST, request.FILES)

        if form.is_valid():
            livro = form.save(commit=False)

            livro.quantidade_disponivel = livro.quantidade_total
            livro.save()

            mensagem_confirmacao = f'Livro {livro.titulo} cadastrado com sucesso!'
            messages.success(request, mensagem_confirmacao)

            return redirect('listar_livros')
    else:
        form = LivroForm()

    dados = {
        'formulario': form
    }

    return render(request, 'cadastrar_livro.html', dados)


@login_required
def editar_livro(request, id):

    livro = Livro.objects.get(id=id)

    form = LivroForm(instance=livro)

    if request.method == 'POST':

        form = LivroForm(request.POST, request.FILES, instance=livro)

        if form.is_valid():
            livro = form.save(commit=False)

            emprestados = livro.emprestimos.filter(status='A').count()
            livro.quantidade_disponivel = livro.quantidade_total - emprestados
            livro.save()

            mensagem_confirmacao = f'Livro {livro.titulo} alterado com sucesso!'
            messages.success(request, mensagem_confirmacao)

            return redirect('listar_livros')

    dados = {
        'formulario': form,
        'livro': livro,
    }

    return render(request, 'editar_livro.html', dados)


@login_required
def remover_livro(request, id):

    livro = Livro.objects.get(id=id)

    if request.method == 'POST':

        if livro.emprestimos.filter(status='A').exists():
            mensagem = f'O livro {livro.titulo} possui exemplares emprestados e não pode ser removido'
            messages.error(request, mensagem)

        else:
            livro.ativo = False
            livro.save()

            mensagem = f'Livro {livro.titulo} removido com sucesso'
            messages.success(request, mensagem)

    return redirect('listar_livros')


@login_required
def livros_removidos(request):

    livros = Livro.objects.filter(
        ativo=False
    ).order_by(Lower('titulo'))

    dados = {
        'livros': livros
    }

    return render(request, 'livros_removidos.html', dados)


@login_required
def restaurar_livro(request, id):

    livro = Livro.objects.get(id=id)

    if request.method == 'POST':
        livro.ativo = True
        livro.save()

        mensagem = f'Livro {livro.titulo} restaurado com sucesso'
        messages.success(request, mensagem)

    return redirect('livros_removidos')


@login_required
def listar_emprestimos(request):

    pesquisa = request.GET.get('pesquisa', '')
    status = request.GET.get('status', 'A')
    ordem = request.GET.get('ordem', 'prevista')

    ordenacoes = {
        'livro': 'livro__titulo',
        'cliente': 'cliente__nome',
        'retirada': 'data_retirada',
        'prevista': 'data_prevista_devolucao',
    }

    campo = ordenacoes.get(ordem.lstrip('-'))
    if campo is None:
        ordem = 'prevista'
        campo = ordenacoes[ordem]
    if ordem.startswith('-'):
        campo = '-' + campo

    emprestimos = Emprestimo.objects.filter(
        Q(cliente__nome__icontains=pesquisa) |
        Q(cliente__cpf__icontains=pesquisa) |
        Q(livro__titulo__icontains=pesquisa)
    ).select_related('cliente', 'livro', 'funcionario').order_by(campo, 'id')

    if status:
        emprestimos = emprestimos.filter(status=status)

    dados = {
        'emprestimos': emprestimos,
        'pesquisa': pesquisa,
        'status': status,
        'ordem': ordem,
        'status_choices': Emprestimo.STATUS_CHOICES,
        'hoje': timezone.localdate(),
    }

    return render(request, 'listar_emprestimos.html', dados)


@login_required
def cadastrar_emprestimo(request):

    if request.method == 'POST':
        form = EmprestimoForm(request.POST)

        if form.is_valid():
            emprestimo = form.save(commit=False)
            emprestimo.funcionario = request.user
            emprestimo.save()

            livro = emprestimo.livro
            livro.quantidade_disponivel = livro.quantidade_disponivel - 1
            livro.save()

            Reserva.objects.filter(
                cliente=emprestimo.cliente,
                livro=livro,
                status__in=['P', 'D'],
            ).update(status='A')

            mensagem_confirmacao = f'Empréstimo do livro {livro.titulo} para {emprestimo.cliente.nome} registrado com sucesso!'
            messages.success(request, mensagem_confirmacao)

            return redirect('listar_emprestimos')
    else:
        form = EmprestimoForm(initial={
            'data_retirada': timezone.localdate(),
            'data_prevista_devolucao': timezone.localdate() + timedelta(days=14),
        })

    dados = {
        'formulario': form
    }

    return render(request, 'cadastrar_emprestimo.html', dados)


@login_required
def devolver_emprestimo(request, id):

    emprestimo = Emprestimo.objects.get(id=id)

    if request.method == 'POST' and emprestimo.status == 'A':
        emprestimo.status = 'D'
        emprestimo.data_devolucao = timezone.localdate()
        emprestimo.save()

        livro = emprestimo.livro
        livro.quantidade_disponivel = livro.quantidade_disponivel + 1
        livro.save()

        mensagem = f'Devolução do livro {livro.titulo} registrada com sucesso'
        messages.success(request, mensagem)

        reserva = Reserva.objects.filter(
            livro=livro,
            status='P'
        ).order_by('data_reserva', 'id').first()

        if reserva:
            reserva.status = 'D'
            reserva.save()

            aviso = f'Avisar {reserva.cliente.nome} (telefone {reserva.cliente.telefone}): o livro {livro.titulo} reservado já está disponível para retirada'
            messages.success(request, aviso)

    return redirect('listar_emprestimos')


@login_required
def renovar_emprestimo(request, id):

    emprestimo = Emprestimo.objects.get(id=id, status='A')

    reservado = Reserva.objects.filter(
        livro=emprestimo.livro,
        status__in=['P', 'D'],
    ).exclude(cliente=emprestimo.cliente).exists()

    if reservado:
        mensagem = f'O livro {emprestimo.livro.titulo} está reservado para outro cliente e não pode ser renovado'
        messages.error(request, mensagem)
        return redirect('listar_emprestimos')

    if request.method == 'POST':
        form = RenovacaoForm(request.POST, emprestimo=emprestimo)

        if form.is_valid():
            emprestimo.data_prevista_devolucao = form.cleaned_data['nova_data_devolucao']
            emprestimo.save()

            mensagem_confirmacao = f'Empréstimo renovado até {emprestimo.data_prevista_devolucao:%d/%m/%Y}!'
            messages.success(request, mensagem_confirmacao)

            return redirect('listar_emprestimos')
    else:
        form = RenovacaoForm(emprestimo=emprestimo)

    dados = {
        'formulario': form,
        'emprestimo': emprestimo,
    }

    return render(request, 'renovar_emprestimo.html', dados)


@login_required
def registrar_ocorrencia(request, id):

    emprestimo = Emprestimo.objects.get(id=id, status='A')

    if request.method == 'POST':
        form = OcorrenciaForm(request.POST)

        if form.is_valid():
            emprestimo.status = form.cleaned_data['ocorrencia']
            emprestimo.observacao = form.cleaned_data['observacao']
            emprestimo.save()

            # O exemplar perdido/danificado sai do acervo
            livro = emprestimo.livro
            if livro.quantidade_total > 0:
                livro.quantidade_total = livro.quantidade_total - 1
                livro.save()

            mensagem_confirmacao = f'Ocorrência registrada para o livro {livro.titulo}'

            if form.cleaned_data['bloquear_cliente']:
                cliente = emprestimo.cliente
                cliente.bloqueado = True
                cliente.save()
                mensagem_confirmacao += f' e cliente {cliente.nome} bloqueado até a regularização'

            messages.success(request, mensagem_confirmacao)

            return redirect('listar_emprestimos')
    else:
        form = OcorrenciaForm()

    dados = {
        'formulario': form,
        'emprestimo': emprestimo,
    }

    return render(request, 'registrar_ocorrencia.html', dados)


@login_required
def listar_reservas(request):

    pesquisa = request.GET.get('pesquisa', '')
    ordem = request.GET.get('ordem', '')

    reservas = Reserva.objects.filter(
        Q(livro__titulo__icontains=pesquisa) | Q(
            cliente__nome__icontains=pesquisa),
        status__in=['P', 'D'],
    ).select_related('cliente', 'livro')

    ordenacoes = {
        'livro': 'livro__titulo',
        'cliente': 'cliente__nome',
    }

    campo = ordenacoes.get(ordem.lstrip('-'))
    if campo is None:
        ordem = ''
        reservas = reservas.order_by('data_reserva', 'id')
    else:
        campo = Lower(campo).desc() if ordem.startswith('-') else Lower(campo).asc()
        reservas = reservas.order_by(campo, 'data_reserva', 'id')

    dados = {
        'reservas': reservas,
        'pesquisa': pesquisa,
        'ordem': ordem,
    }

    return render(request, 'listar_reservas.html', dados)


@login_required
def cadastrar_reserva(request):

    if request.method == 'POST':
        form = ReservaForm(request.POST)

        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.funcionario = request.user
            reserva.save()

            mensagem_confirmacao = f'Reserva do livro {reserva.livro.titulo} para {reserva.cliente.nome} registrada com sucesso!'
            messages.success(request, mensagem_confirmacao)

            return redirect('listar_reservas')
    else:
        form = ReservaForm()

    dados = {
        'formulario': form
    }

    return render(request, 'cadastrar_reserva.html', dados)


@login_required
def cancelar_reserva(request, id):

    reserva = Reserva.objects.get(id=id)

    if request.method == 'POST' and reserva.status in ['P', 'D']:
        estava_disponivel = reserva.status == 'D'

        reserva.status = 'C'
        reserva.save()

        mensagem = f'Reserva do livro {reserva.livro.titulo} para {reserva.cliente.nome} cancelada com sucesso'
        messages.success(request, mensagem)

        if estava_disponivel:
            proxima = Reserva.objects.filter(
                livro=reserva.livro,
                status='P'
            ).order_by('data_reserva', 'id').first()

            if proxima:
                proxima.status = 'D'
                proxima.save()

                aviso = f'Avisar {proxima.cliente.nome} (telefone {proxima.cliente.telefone}): o livro {proxima.livro.titulo} já está disponível para retirada'
                messages.success(request, aviso)

    return redirect('listar_reservas')


@login_required
def relatorios(request):

    if not request.user.is_superuser:
        messages.error(
            request, 'Acesso permitido somente para administradores.')
        return redirect('index')

    form = RelatorioForm(request.GET or None)

    emprestimos = Emprestimo.objects.all()
    tipo = 'livros'

    if form.is_valid():
        data_inicial = form.cleaned_data['data_inicial']
        data_final = form.cleaned_data['data_final']
        tipo = form.cleaned_data['tipo'] or 'livros'

        if data_inicial:
            emprestimos = emprestimos.filter(data_retirada__gte=data_inicial)

        if data_final:
            emprestimos = emprestimos.filter(data_retirada__lte=data_final)

    livros_mais_emprestados = emprestimos.values(
        'livro__titulo',
        'livro__autor',
    ).annotate(total=Count('id')).order_by('-total', 'livro__titulo')

    clientes_mais_emprestimos = emprestimos.values(
        'cliente__nome',
        'cliente__cpf',
    ).annotate(total=Count('id')).order_by('-total', 'cliente__nome')

    dados = {
        'form': form,
        'tipo': tipo,
        'total_emprestimos': emprestimos.count(),
        'livros_mais_emprestados': livros_mais_emprestados,
        'clientes_mais_emprestimos': clientes_mais_emprestimos,
        'emprestimos': emprestimos.select_related('cliente', 'livro').order_by('-data_retirada'),
    }

    return render(request, 'relatorios.html', dados)
