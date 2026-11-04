from django.contrib import messages
from functools import wraps

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, F
from django.shortcuts import redirect, render
from django.utils import timezone
from .forms import EmprestimoForm, FuncionarioCreationForm, FuncionarioEditForm, ClienteForm, LivroForm, OcorrenciaForm, RelatorioForm, RenovacaoForm, ReservaForm
from .models import Cliente, Emprestimo, Livro, Reserva


def funcionario_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view(request, *args, **kwargs)
        return redirect('login')

    return login_required(wrapped)


def administrador_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view(request, *args, **kwargs)
        return redirect('index')

    return login_required(wrapped)


@funcionario_required
def index(request):
    dados = {
        'livros_disponiveis': Livro.objects.count(),
        'clientes_ativos': Cliente.objects.filter(ativo=True).count(),
        'emprestimos_ativos': Emprestimo.objects.filter(status='A').count(),
        'reservas_disponiveis': Reserva.objects.filter(status='D').count(),
    }
    return render(request, 'index.html', dados)


@funcionario_required
def listar_clientes(request):
    pesquisa = request.GET.get('pesquisa', '')
    clientes = Cliente.objects.filter(nome__icontains=pesquisa).order_by('nome')
    return render(request, 'clientes.html', {'clientes': clientes, 'pesquisa': pesquisa})


@funcionario_required
def cadastrar_cliente(request):
    form = ClienteForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente cadastrado com sucesso.')
        return redirect('listar_clientes')

    return render(request, 'formulario.html', {'form': form, 'titulo': 'Cadastrar cliente'})


@funcionario_required
def editar_cliente(request, id):
    cliente = Cliente.objects.get(id=id)
    form = ClienteForm(request.POST or None, instance=cliente)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente alterado com sucesso.')
        return redirect('listar_clientes')

    return render(request, 'formulario.html', {'form': form, 'titulo': 'Editar cliente'})


@funcionario_required
def listar_livros(request):
    pesquisa = request.GET.get('pesquisa', '')
    todos = request.GET.get('todos') == '1'

    livros = Livro.objects.all() if todos else Livro.objects.filter(ativo=True)
    livros = (
        livros.filter(titulo__icontains=pesquisa)
        | livros.filter(autor__icontains=pesquisa)
        | livros.filter(genero__icontains=pesquisa)
        | livros.filter(isbn__icontains=pesquisa)
    )

    return render(
        request,
        'livros.html',
        {'livros': livros.distinct().order_by('titulo'), 'pesquisa': pesquisa, 'todos': todos},
    )


@funcionario_required
def cadastrar_livro(request):
    form = LivroForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        livro = form.save()
        messages.success(request, f'Livro {livro.titulo} cadastrado com sucesso.')
        return redirect('listar_livros')

    return render(request, 'formulario.html', {'form': form, 'titulo': 'Cadastrar livro', 'tem_arquivo': True})


@funcionario_required
def editar_livro(request, id):
    livro = Livro.objects.get(id=id)
    form = LivroForm(request.POST or None, request.FILES or None, instance=livro)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Livro alterado com sucesso.')
        return redirect('listar_livros')

    return render(request, 'formulario.html', {'form': form, 'titulo': 'Editar livro', 'tem_arquivo': True})


@funcionario_required
def excluir_livro(request, id):
    livro = Livro.objects.get(id=id)

    if request.method == 'POST':
        if livro.emprestimos.filter(status='A').exists():
            messages.error(request, 'Não é possível remover um livro com exemplares emprestados.')
        else:
            livro.ativo = False
            livro.save()
            messages.success(request, 'Livro removido do catálogo. O histórico foi preservado.')

    return redirect('listar_livros')


@funcionario_required
def listar_emprestimos(request):
    emprestimos = Emprestimo.objects.select_related('cliente', 'livro', 'funcionario').order_by('-data_retirada')
    form = EmprestimoForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            livro = Livro.objects.select_for_update().get(id=form.cleaned_data['livro'].id)
            reserva = Reserva.objects.filter(livro=livro, status='DISPONIVEL').order_by('data_reserva', 'id').first()
            cliente = form.cleaned_data['cliente']

            if livro.quantidade_disponivel < 1:
                form.add_error('livro', 'Não há exemplares disponíveis deste livro.')
            elif reserva and reserva.cliente_id != cliente.id:
                form.add_error('livro', 'Este exemplar está reservado para outro cliente.')
            else:
                emprestimo = form.save(commit=False)
                emprestimo.funcionario = request.user
                emprestimo.livro = livro
                emprestimo.save()
                Livro.objects.filter(id=livro.id).update(quantidade_disponivel=F('quantidade_disponivel') - 1)

                if reserva:
                    reserva.status = 'ATENDIDA'
                    reserva.save()

                messages.success(request, 'Empréstimo registrado com sucesso.')
                return redirect('listar_emprestimos')

    return render(request, 'emprestimos.html', {'emprestimos': emprestimos, 'form': form})


@funcionario_required
def devolver_emprestimo(request, id):
    emprestimo = Emprestimo.objects.get(id=id, status='A')

    if request.method == 'POST':
        with transaction.atomic():
            emprestimo.status = 'D'
            emprestimo.data_devolucao = timezone.localdate()
            emprestimo.save()
            Livro.objects.filter(id=emprestimo.livro_id).update(quantidade_disponivel=F('quantidade_disponivel') + 1)

            reserva = Reserva.objects.filter(livro=emprestimo.livro, status='P').order_by('data_reserva', 'id').first()
            if reserva:
                reserva.status = 'D'
                reserva.save()
                messages.success(request, 'Devolução registrada. A reserva de ' + reserva.cliente.nome + ' está disponível para retirada.')
            else:
                messages.success(request, 'Devolução registrada com sucesso.')

    return redirect('listar_emprestimos')


@funcionario_required
def renovar_emprestimo(request, id):
    emprestimo = Emprestimo.objects.get(id=id, status='A')
    form = RenovacaoForm(request.POST or None, emprestimo=emprestimo)
    reserva = Reserva.objects.filter(
        livro=emprestimo.livro,
        status__in=['P', 'D'],
    ).exclude(cliente=emprestimo.cliente).exists()

    if reserva:
        form.add_error(None, 'Este livro possui reserva de outro cliente e não pode ser renovado.')
    elif request.method == 'POST' and form.is_valid():
        emprestimo.data_prevista_devolucao = form.cleaned_data['nova_data_devolucao']
        emprestimo.save()
        messages.success(request, 'Empréstimo renovado com sucesso.')
        return redirect('listar_emprestimos')

    return render(request, 'formulario.html', {'form': form, 'titulo': 'Renovar empréstimo'})


@funcionario_required
def registrar_ocorrencia(request, id):
    emprestimo = Emprestimo.objects.get(id=id, status='ATIVO')
    form = OcorrenciaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        emprestimo.status = form.cleaned_data['ocorrencia']
        emprestimo.observacao = form.cleaned_data['observacao']
        emprestimo.save()
        emprestimo.cliente.bloqueado = True
        emprestimo.cliente.save()
        messages.success(request, 'Ocorrência registrada e cliente bloqueado.')
        return redirect('listar_emprestimos')

    return render(request, 'formulario.html', {'form': form, 'titulo': 'Registrar perda ou dano'})


@funcionario_required
def listar_reservas(request):
    reservas = Reserva.objects.select_related('cliente', 'livro').order_by('-data_reserva')
    form = ReservaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        reserva = form.save(commit=False)
        reserva.funcionario = request.user
        reserva.save()
        messages.success(request, 'Reserva registrada com sucesso.')
        return redirect('listar_reservas')

    return render(request, 'reservas.html', {'reservas': reservas, 'form': form})


@funcionario_required
def cancelar_reserva(request, id):
    reserva = Reserva.objects.get(id=id, status__in=['PENDENTE', 'DISPONIVEL'])

    if request.method == 'POST':
        reserva.status = 'CANCELADA'
        reserva.save()
        messages.success(request, 'Reserva cancelada.')

    return redirect('listar_reservas')


@administrador_required
def listar_funcionarios(request):
    funcionarios = User.objects.filter(is_staff=True).order_by('username')
    return render(request, 'funcionarios.html', {'funcionarios': funcionarios})


@administrador_required
def cadastrar_funcionario(request):
    form = FuncionarioCreationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        funcionario = form.save(commit=False)
        funcionario.is_staff = True
        funcionario.save()
        messages.success(request, 'Funcionário cadastrado com sucesso.')
        return redirect('listar_funcionarios')

    return render(request, 'formulario.html', {'form': form, 'titulo': 'Cadastrar funcionário'})


@administrador_required
def editar_funcionario(request, id):
    funcionario = User.objects.get(id=id, is_staff=True)
    form = FuncionarioEditForm(request.POST or None, instance=funcionario)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Funcionário alterado com sucesso.')
        return redirect('listar_funcionarios')

    return render(request, 'formulario.html', {'form': form, 'titulo': 'Editar funcionário'})


@administrador_required
def relatorios(request):
    form = RelatorioForm(request.GET or None)
    emprestimos = Emprestimo.objects.all()

    if form.is_valid():
        if form.cleaned_data.get('data_inicial'):
            emprestimos = emprestimos.filter(data_retirada__gte=form.cleaned_data['data_inicial'])
        if form.cleaned_data.get('data_final'):
            emprestimos = emprestimos.filter(data_retirada__lte=form.cleaned_data['data_final'])

    livros_mais_emprestados = emprestimos.values('livro__titulo').annotate(total=Count('id')).order_by('-total')[:10]
    clientes_mais_emprestimos = emprestimos.values('cliente__nome').annotate(total=Count('id')).order_by('-total')[:10]

    return render(request, 'relatorios.html', {
        'form': form,
        'livros_mais_emprestados': livros_mais_emprestados,
        'clientes_mais_emprestimos': clientes_mais_emprestimos,
        'total_emprestimos': emprestimos.count(),
    })


def sair(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')

    return redirect('login')

