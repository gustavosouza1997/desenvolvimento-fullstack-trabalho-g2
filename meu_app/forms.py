from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import Usuario, Livro, Emprestimo, Reserva

class UsuarioForm(forms.ModelForm):

    class Meta:
        model = Usuario
        fields = [
            'nome',
            'cpf',
            'telefone',
            'endereco',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome completo'
            }),

            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00',
                'data-mascara': 'cpf',
                'inputmode': 'numeric',
                'maxlength': '14',
                'autocomplete': 'off',
            }),

            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000',
                'data-mascara': 'telefone',
                'inputmode': 'tel',
                'maxlength': '15',
            }),

            'endereco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rua, número, bairro, cidade'
            }),
        }

    def clean_cpf(self):
        numeros = ''.join(c for c in self.cleaned_data['cpf'] if c.isdigit())

        if len(numeros) != 11:
            raise forms.ValidationError('O CPF deve ter 11 dígitos.')

        cpf = f'{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}'

        outros_usuarios = Usuario.objects.filter(cpf__in=[cpf, numeros])
        if self.instance.pk:
            outros_usuarios = outros_usuarios.exclude(pk=self.instance.pk)

        usuario_existente = outros_usuarios.first()
        if usuario_existente:
            situacao = '' if usuario_existente.ativo else ' (inativo)'
            raise forms.ValidationError(f'Este CPF já está cadastrado para {usuario_existente.nome}{situacao}.')

        return cpf

    def clean_telefone(self):
        numeros = ''.join(c for c in self.cleaned_data['telefone'] if c.isdigit())

        if len(numeros) not in (10, 11):
            raise forms.ValidationError('Informe o telefone com DDD, por exemplo (51) 99999-9999.')

        if len(numeros) == 11:
            return f'({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}'
        return f'({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}'


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
        ]

        labels = {
            'ano_publicacao': 'Ano de publicação',
            'isbn': 'ISBN',
            'genero': 'Gênero',
            'quantidade_total': 'Quantidade',
        }

        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título do livro'
            }),

            'autor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do autor'
            }),

            'editora': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'ano_publicacao': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'isbn': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'genero': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'quantidade_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
        }

    def clean_quantidade_total(self):
        quantidade_total = self.cleaned_data['quantidade_total']

        if self.instance.pk:
            emprestados = self.instance.emprestimos.filter(status='A').count()

            if quantidade_total < emprestados:
                raise forms.ValidationError(
                    f'Existem {emprestados} exemplares emprestados. A quantidade não pode ser menor que isso.'
                )

        return quantidade_total


class EmprestimoForm(forms.ModelForm):

    class Meta:
        model = Emprestimo
        fields = [
            'usuario',
            'livro',
            'data_retirada',
            'data_prevista_devolucao',
        ]

        labels = {
            'data_retirada': 'Data de retirada',
            'data_prevista_devolucao': 'Data prevista para devolução',
        }

        widgets = {
            'usuario': forms.Select(attrs={
                'class': 'form-select'
            }),

            'livro': forms.Select(attrs={
                'class': 'form-select'
            }),

            'data_retirada': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'form-control'
            }),

            'data_prevista_devolucao': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['usuario'].queryset = Usuario.objects.filter(ativo=True, bloqueado=False).order_by('nome')
        self.fields['livro'].queryset = Livro.objects.filter(ativo=True, quantidade_disponivel__gt=0).order_by('titulo')

    def clean(self):
        dados = super().clean()

        usuario = dados.get('usuario')
        livro = dados.get('livro')
        data_retirada = dados.get('data_retirada')
        data_prevista = dados.get('data_prevista_devolucao')

        if data_retirada and data_prevista and data_prevista <= data_retirada:
            self.add_error('data_prevista_devolucao', 'A devolução deve ser depois da data de retirada.')

        if usuario and livro:
            reserva = Reserva.objects.filter(livro=livro, status='D').order_by('data_reserva', 'id').first()

            if reserva and reserva.usuario != usuario:
                self.add_error('livro', f'Este livro está reservado para {reserva.usuario.nome}.')

        return dados


class ReservaForm(forms.ModelForm):

    class Meta:
        model = Reserva
        fields = [
            'usuario',
            'livro',
        ]

        widgets = {
            'usuario': forms.Select(attrs={
                'class': 'form-select'
            }),

            'livro': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['usuario'].queryset = Usuario.objects.filter(ativo=True, bloqueado=False).order_by('nome')
        self.fields['livro'].queryset = Livro.objects.filter(ativo=True, quantidade_disponivel=0).order_by('titulo')

    def clean(self):
        dados = super().clean()

        usuario = dados.get('usuario')
        livro = dados.get('livro')

        if usuario and livro:
            ja_reservado = Reserva.objects.filter(
                usuario=usuario,
                livro=livro,
                status__in=['P', 'D'],
            ).exists()

            if ja_reservado:
                self.add_error('livro', 'Este usuário já possui uma reserva ativa para este livro.')

        return dados


class RenovacaoForm(forms.Form):

    nova_data_devolucao = forms.DateField(
        label='Nova data de devolução',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        self.emprestimo = kwargs.pop('emprestimo')
        super().__init__(*args, **kwargs)

    def clean_nova_data_devolucao(self):
        nova_data = self.cleaned_data['nova_data_devolucao']

        if nova_data <= self.emprestimo.data_prevista_devolucao:
            raise forms.ValidationError('A nova data deve ser depois da data de devolução atual.')

        if nova_data <= timezone.localdate():
            raise forms.ValidationError('A nova data deve ser uma data futura.')

        return nova_data


OCORRENCIA_CHOICES = [
    ('P', 'Perdido'),
    ('X', 'Danificado'),
]


class OcorrenciaForm(forms.Form):

    ocorrencia = forms.ChoiceField(
        label='Ocorrência',
        choices=OCORRENCIA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    observacao = forms.CharField(
        label='Observação',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control'
        })
    )

    bloquear_usuario = forms.BooleanField(
        label='Bloquear usuário até a regularização',
        required=False,
        initial=True
    )


class FuncionarioForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
        ]


class EditarFuncionarioForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
        ]


TIPO_RELATORIO_CHOICES = [
    ('livros', 'Livros mais emprestados'),
    ('usuarios', 'Usuários com mais empréstimos'),
    ('emprestimos', 'Todos os empréstimos do período'),
]


class RelatorioForm(forms.Form):

    tipo = forms.ChoiceField(
        label='Relatório',
        choices=TIPO_RELATORIO_CHOICES,
        required=False
    )

    data_inicial = forms.DateField(
        label='Data inicial',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date'
        })
    )

    data_final = forms.DateField(
        label='Data final',
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date'
        })
    )

    def clean(self):
        dados = super().clean()

        data_inicial = dados.get('data_inicial')
        data_final = dados.get('data_final')

        if data_inicial and data_final and data_final < data_inicial:
            self.add_error('data_final', 'A data final deve ser igual ou depois da data inicial.')

        return dados
