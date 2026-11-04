from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import Cliente, Emprestimo, Livro, Reserva


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'cpf', 'telefone', 'endereco', 'ativo', 'bloqueado']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
        }


class LivroForm(forms.ModelForm):
    class Meta:
        model = Livro
        fields = [
            'titulo',
            'autor',
            'editora',
            'ano_publicacao',
            'isbn',
            'genero',
            'quantidade_total',
            'capa',
            'ativo',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'autor': forms.TextInput(attrs={'class': 'form-control'}),
            'editora': forms.TextInput(attrs={'class': 'form-control'}),
            'ano_publicacao': forms.NumberInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'genero': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade_total': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        dados = super().clean()
        quantidade_total = dados.get('quantidade_total')
        livro = self.instance
        emprestados = livro.emprestimos.filter(status='ATIVO').count() if livro.pk else 0

        if quantidade_total is not None and quantidade_total < emprestados:
            self.add_error('quantidade_total', 'A quantidade não pode ser menor que os exemplares emprestados.')

        return dados

    def save(self, commit=True):
        livro = super().save(commit=False)
        emprestados = livro.emprestimos.filter(status='ATIVO').count() if livro.pk else 0
        livro.quantidade_disponivel = livro.quantidade_total - emprestados

        if commit:
            livro.save()
            self.save_m2m()

        return livro


class EmprestimoForm(forms.ModelForm):
    class Meta:
        model = Emprestimo
        fields = ['cliente', 'livro', 'data_retirada', 'data_prevista_devolucao']
        widgets = {
            'data_retirada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_prevista_devolucao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True, bloqueado=False)
        self.fields['livro'].queryset = Livro.objects.filter(ativo=True)

    def clean(self):
        dados = super().clean()
        cliente = dados.get('cliente')
        livro = dados.get('livro')
        retirada = dados.get('data_retirada')
        devolucao = dados.get('data_prevista_devolucao')

        if retirada and devolucao and devolucao <= retirada:
            self.add_error('data_prevista_devolucao', 'A devolução deve ser posterior à retirada.')

        if livro and livro.quantidade_disponivel < 1:
            self.add_error('livro', 'Não há exemplares disponíveis deste livro.')

        if livro:
            reserva = Reserva.objects.filter(livro=livro, status='DISPONIVEL').order_by('data_reserva', 'id').first()
            if reserva and cliente and reserva.cliente_id != cliente.id:
                self.add_error('livro', 'Este exemplar está reservado para outro cliente.')

        return dados


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['cliente', 'livro']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True, bloqueado=False)
        self.fields['livro'].queryset = Livro.objects.filter(ativo=True)

    def clean(self):
        dados = super().clean()
        cliente = dados.get('cliente')
        livro = dados.get('livro')

        if livro and livro.quantidade_disponivel > 0:
            self.add_error('livro', 'Só é possível reservar livros sem exemplares disponíveis.')

        if cliente and livro and Reserva.objects.filter(
            cliente=cliente,
            livro=livro,
            status__in=['PENDENTE', 'DISPONIVEL'],
        ).exists():
            self.add_error('livro', 'Este cliente já possui uma reserva ativa para o livro.')

        return dados


class RenovacaoForm(forms.Form):
    nova_data_devolucao = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, emprestimo=None, **kwargs):
        self.emprestimo = emprestimo
        super().__init__(*args, **kwargs)

    def clean_nova_data_devolucao(self):
        nova_data = self.cleaned_data['nova_data_devolucao']

        if self.emprestimo and nova_data <= self.emprestimo.data_prevista_devolucao:
            raise forms.ValidationError('A nova data deve ser posterior à data atual de devolução.')

        if nova_data <= timezone.localdate():
            raise forms.ValidationError('A nova data deve ser futura.')

        return nova_data


class OcorrenciaForm(forms.Form):
    ocorrencia = forms.ChoiceField(choices=[('PERDIDO', 'Perdido'), ('DANIFICADO', 'Danificado')])
    observacao = forms.CharField(widget=forms.Textarea, required=False)


class FuncionarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email']


class FuncionarioEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']


class RelatorioForm(forms.Form):
    data_inicial = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    data_final = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def clean(self):
        dados = super().clean()
        inicial = dados.get('data_inicial')
        final = dados.get('data_final')

        if inicial and final and final < inicial:
            self.add_error('data_final', 'A data final deve ser igual ou posterior à inicial.')

        return dados