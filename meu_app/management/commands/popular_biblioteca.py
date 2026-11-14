from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from meu_app.models import Cliente, Emprestimo, Livro, Reserva


SENHA_FUNCIONARIOS = 'Biblioteca@2026'

# (username, nome, sobrenome, ativo)
FUNCIONARIOS = [
    ('mariana.lopes', 'Mariana', 'Lopes', True),
    ('joao.vargas', 'João', 'Vargas', True),
    ('helena.becker', 'Helena', 'Becker', False),  # testa "funcionários inativos"
]

# (titulo, autor, editora, ano, isbn, genero, quantidade_total, ativo)
LIVROS = [
    ('Dom Casmurro', 'Machado de Assis', 'Penguin-Companhia', 2016, '9788582850350', 'Romance', 3, True),
    ('Memórias Póstumas de Brás Cubas', 'Machado de Assis', 'Penguin-Companhia', 2014, '9788582850435', 'Romance', 2, True),
    ('O Cortiço', 'Aluísio Azevedo', 'Ática', 1997, '9788508126194', 'Romance', 2, True),
    ('Vidas Secas', 'Graciliano Ramos', 'Record', 2019, '9788501114785', 'Romance', 2, True),
    ('Grande Sertão: Veredas', 'João Guimarães Rosa', 'Companhia das Letras', 2019, '9788535932171', 'Romance', 1, True),
    ('A Hora da Estrela', 'Clarice Lispector', 'Rocco', 2020, '9786555320428', 'Romance', 2, True),
    ('Capitães da Areia', 'Jorge Amado', 'Companhia das Letras', 2008, '9788535911695', 'Romance', 2, True),
    ('O Auto da Compadecida', 'Ariano Suassuna', 'Nova Fronteira', 2018, '9788520943243', 'Teatro', 1, True),
    ('Macunaíma', 'Mário de Andrade', 'Penguin-Companhia', 2016, '9788582850480', 'Romance', 1, False),
    ('Quarto de Despejo', 'Carolina Maria de Jesus', 'Ática', 2014, '9788508171279', 'Biografia', 2, True),
    ('1984', 'George Orwell', 'Companhia das Letras', 2009, '9788535914849', 'Ficção Científica', 3, True),
    ('A Revolução dos Bichos', 'George Orwell', 'Companhia das Letras', 2007, '9788535909555', 'Fábula', 2, True),
    ('Cem Anos de Solidão', 'Gabriel García Márquez', 'Record', 2019, '9788501012074', 'Realismo Mágico', 1, True),
    ('O Pequeno Príncipe', 'Antoine de Saint-Exupéry', 'Agir', 2015, '9788522008735', 'Infantojuvenil', 2, True),
    ('O Hobbit', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2019, '9788595084742', 'Fantasia', 2, True),
    ('A Sociedade do Anel', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2019, '9788595084759', 'Fantasia', 1, True),
    ('Harry Potter e a Pedra Filosofal', 'J.K. Rowling', 'Rocco', 2017, '9788532530783', 'Fantasia', 3, True),
    ('Orgulho e Preconceito', 'Jane Austen', 'Martin Claret', 2018, '9788544001486', 'Romance', 2, True),
    ('Crime e Castigo', 'Fiódor Dostoiévski', 'Editora 34', 2016, '9788573264463', 'Romance', 1, True),
    ('O Alquimista', 'Paulo Coelho', 'Paralela', 2017, '9788584390670', 'Ficção', 2, True),
    ('Ensaio Sobre a Cegueira', 'José Saramago', 'Companhia das Letras', 2020, '9788535930115', 'Romance', 1, True),
    ('Sapiens: Uma Breve História da Humanidade', 'Yuval Noah Harari', 'L&PM', 2015, '9788525432186', 'História', 2, True),
    ('O Diário de Anne Frank', 'Anne Frank', 'Record', 2015, '9788501044457', 'Biografia', 2, True),
    ('Fahrenheit 451', 'Ray Bradbury', 'Biblioteca Azul', 2012, '9788525052247', 'Ficção Científica', 1, True),
    ('Admirável Mundo Novo', 'Aldous Huxley', 'Biblioteca Azul', 2014, '9788525056009', 'Ficção Científica', 1, True),
    ('O Nome do Vento', 'Patrick Rothfuss', 'Arqueiro', 2009, '9788599296493', 'Fantasia', 1, True),
    ('Torto Arado', 'Itamar Vieira Junior', 'Todavia', 2019, '9786580309313', 'Romance', 2, True),
    ('O Mundo de Sofia', 'Jostein Gaarder', 'Companhia das Letras', 1995, '9788571644694', 'Filosofia', 1, False),
    ('Duna', 'Frank Herbert', 'Aleph', 2017, '9788576573135', 'Ficção Científica', 2, True),
    ('A Menina que Roubava Livros', 'Markus Zusak', 'Intrínseca', 2007, '9788598078175', 'Romance', 1, True),
    # Harry Potter
    ('Harry Potter e a Câmara Secreta', 'J.K. Rowling', 'Rocco', 2017, '9788564102378', 'Fantasia', 3, True),
    ('Harry Potter e o Prisioneiro de Azkaban', 'J.K. Rowling', 'Rocco', 2017, '9788564102743', 'Fantasia', 2, True),
    ('Harry Potter e o Cálice de Fogo', 'J.K. Rowling', 'Rocco', 2017, '9788564103115', 'Fantasia', 2, True),
    ('Harry Potter e a Ordem da Fênix', 'J.K. Rowling', 'Rocco', 2017, '9788564103481', 'Fantasia', 2, True),
    ('Harry Potter e o Enigma do Príncipe', 'J.K. Rowling', 'Rocco', 2017, '9788564103856', 'Fantasia', 2, True),
    ('Harry Potter e as Relíquias da Morte', 'J.K. Rowling', 'Rocco', 2017, '9788564104228', 'Fantasia', 2, True),
    # Ciclo da Herança (Eragon)
    ('Eragon', 'Christopher Paolini', 'Rocco', 2005, '9788564104594', 'Fantasia', 2, True),
    ('Eldest', 'Christopher Paolini', 'Rocco', 2006, '9788564104969', 'Fantasia', 1, True),
    ('Brisingr', 'Christopher Paolini', 'Rocco', 2009, '9788564105331', 'Fantasia', 1, True),
    ('Herança', 'Christopher Paolini', 'Rocco', 2012, '9788564105706', 'Fantasia', 1, True),
    ('O Garfo, a Bruxa e o Dragão', 'Christopher Paolini', 'Rocco', 2019, '9788564106079', 'Fantasia', 1, True),
    ('Murtagh', 'Christopher Paolini', 'Rocco', 2023, '9788564106444', 'Fantasia', 1, True),
    # Patrick Rothfuss
    ('O Temor do Sábio', 'Patrick Rothfuss', 'Arqueiro', 2011, '9788564106819', 'Fantasia', 1, True),
    ('A Música do Silêncio', 'Patrick Rothfuss', 'Arqueiro', 2014, '9788564107182', 'Fantasia', 1, True),
    ('O Estreito Caminho Entre Desejos', 'Patrick Rothfuss', 'Arqueiro', 2023, '9788564107557', 'Fantasia', 1, True),
    # Tolkien / Terra-média
    ('As Duas Torres', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2019, '9788564107922', 'Fantasia', 1, True),
    ('O Retorno do Rei', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2019, '9788564108295', 'Fantasia', 1, True),
    ('O Silmarillion', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2019, '9788564108660', 'Fantasia', 2, True),
    ('Contos Inacabados', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2020, '9788564109032', 'Fantasia', 1, True),
    ('Os Filhos de Húrin', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2020, '9788564109407', 'Fantasia', 1, True),
    ('Beren e Lúthien', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2018, '9788564109773', 'Fantasia', 1, True),
    ('A Queda de Gondolin', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2019, '9788564110144', 'Fantasia', 1, True),
    ('A Natureza da Terra-média', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2021, '9788564110519', 'Fantasia', 1, True),
    ('A Queda de Númenor', 'J.R.R. Tolkien', 'HarperCollins Brasil', 2022, '9788564110885', 'Fantasia', 1, True),
    # John Flanagan (Rangers - Ordem dos Arqueiros)
    ('Rangers: Ruínas de Gorlan', 'John Flanagan', 'Fundamento', 2009, '9788564111257', 'Infantojuvenil', 2, True),
    ('Rangers: A Ponte em Chamas', 'John Flanagan', 'Fundamento', 2009, '9788564111622', 'Infantojuvenil', 1, True),
    ('Rangers: Terra do Gelo', 'John Flanagan', 'Fundamento', 2010, '9788564111998', 'Infantojuvenil', 1, True),
    ('Rangers: Folha de Carvalho', 'John Flanagan', 'Fundamento', 2010, '9788564112360', 'Infantojuvenil', 1, True),
    ('Rangers: Feiticeiro do Norte', 'John Flanagan', 'Fundamento', 2011, '9788564112735', 'Infantojuvenil', 1, True),
    ('Rangers: Cerco a Macindaw', 'John Flanagan', 'Fundamento', 2011, '9788564113107', 'Infantojuvenil', 1, True),
    ('Rangers: Resgate de Erak', 'John Flanagan', 'Fundamento', 2012, '9788564113473', 'Infantojuvenil', 1, True),
    ('Rangers: Os Reis de Clonmel', 'John Flanagan', 'Fundamento', 2012, '9788564113848', 'Infantojuvenil', 1, True),
    ('Rangers: Halt em Perigo', 'John Flanagan', 'Fundamento', 2013, '9788564114210', 'Infantojuvenil', 1, True),
    ('Rangers: O Imperador de Nihon-Ja', 'John Flanagan', 'Fundamento', 2013, '9788564114586', 'Infantojuvenil', 1, True),
    ('Rangers: Histórias Perdidas', 'John Flanagan', 'Fundamento', 2014, '9788564114951', 'Infantojuvenil', 1, True),
    ('Rangers: O Arqueiro do Rei', 'John Flanagan', 'Fundamento', 2015, '9788564115323', 'Infantojuvenil', 1, True),
    # The Witcher
    ('O Último Desejo', 'Andrzej Sapkowski', 'WMF Martins Fontes', 2011, '9788564115699', 'Fantasia', 2, True),
    ('A Espada do Destino', 'Andrzej Sapkowski', 'WMF Martins Fontes', 2012, '9788564116061', 'Fantasia', 1, True),
    ('O Sangue dos Elfos', 'Andrzej Sapkowski', 'WMF Martins Fontes', 2013, '9788564116436', 'Fantasia', 1, True),
    ('Tempo do Desprezo', 'Andrzej Sapkowski', 'WMF Martins Fontes', 2014, '9788564116801', 'Fantasia', 1, True),
    ('Batismo de Fogo', 'Andrzej Sapkowski', 'WMF Martins Fontes', 2014, '9788564117174', 'Fantasia', 1, True),
    ('A Torre da Andorinha', 'Andrzej Sapkowski', 'WMF Martins Fontes', 2016, '9788564117549', 'Fantasia', 1, True),
    ('A Senhora do Lago', 'Andrzej Sapkowski', 'WMF Martins Fontes', 2017, '9788564117914', 'Fantasia', 1, True),
    ('Tempo de Tempestade', 'Andrzej Sapkowski', 'WMF Martins Fontes', 2019, '9788564118287', 'Fantasia', 1, True),
]

# (apelido, nome, base do CPF, telefone, endereço, ativo, bloqueado)
CLIENTES = [
    ('ana', 'Ana Beatriz Moreira', '483915026', '(51) 99634-1187', 'Rua Tristão Monteiro, 1250 - Centro, Taquara/RS', True, False),
    ('rafael', 'Rafael Lindemann', '701264839', '(51) 98417-5520', 'Avenida Sebastião Amoretti, 3420 - Parobé/RS', True, False),
    ('juliana', 'Juliana Kessler Prado', '362890174', '(51) 99288-4361', 'Rua Júlio de Castilhos, 877 - Centro, Taquara/RS', True, False),
    ('thiago', 'Thiago Bortolini', '915037428', '(51) 98102-7745', 'Rua Pinheiro Machado, 215 - Igrejinha/RS', True, False),
    ('camila', 'Camila Fagundes', '248613907', '(51) 99751-0396', 'Rua Coronel Frederico Linck, 1902 - Rio Branco, Taquara/RS', True, False),
    ('lucas', 'Lucas Weber Schmitt', '630481752', '(51) 98563-2218', 'Rua Mundo Novo, 66 - Tucanos, Taquara/RS', True, False),
    ('patricia', 'Patrícia Nunes Dalla Rosa', '157049386', '(51) 99920-6473', 'Avenida Oscar Martins Rangel, 1540 - Santo Antônio da Patrulha/RS', True, False),
    ('eduardo', 'Eduardo Hoffmann', '894726103', '(51) 98839-9012', 'Rua Guilherme Lahm, 401 - Centro, Rolante/RS', True, False),
    ('fernanda', 'Fernanda Zanatta', '527368190', '(51) 99147-8854', 'Rua Marechal Floriano, 1033 - Centro, Gramado/RS', False, False),
    ('marcelo', 'Marcelo Azambuja', '076152948', '(51) 98276-3309', 'Rua Rio Branco, 588 - Santa Teresinha, Taquara/RS', True, True),
]

# (cliente, isbn do livro, dias retirada, dias prevista, dias devolução, status, funcionário, observação)
# Os dias são relativos a hoje (negativo = passado).
EMPRESTIMOS = [
    # Histórico de devolvidos (alimenta os relatórios)
    ('patricia', '9788582850480', -160, -146, -147, 'D', 'mariana.lopes', ''),
    ('ana', '9788582850350', -150, -136, -138, 'D', 'mariana.lopes', ''),
    ('thiago', '9788535914849', -140, -126, -126, 'D', 'joao.vargas', ''),
    ('camila', '9788532530783', -130, -116, -117, 'D', 'helena.becker', ''),
    ('fernanda', '9788544001486', -125, -111, -112, 'D', 'helena.becker', ''),
    ('rafael', '9788582850350', -120, -106, -108, 'D', 'joao.vargas', ''),
    ('eduardo', '9788584390670', -110, -96, -100, 'D', 'mariana.lopes', ''),
    ('fernanda', '9788535914849', -100, -86, -84, 'D', 'joao.vargas', ''),
    ('marcelo', '9788501114785', -95, -81, -83, 'D', 'mariana.lopes', ''),
    ('patricia', '9786555320428', -90, -76, -80, 'D', 'joao.vargas', ''),
    ('ana', '9788525432186', -75, -61, -65, 'D', 'mariana.lopes', ''),
    ('lucas', '9788532530783', -70, -56, -60, 'D', 'joao.vargas', ''),
    ('juliana', '9788535911695', -55, -41, -44, 'D', 'mariana.lopes', ''),
    ('juliana', '9788582850350', -40, -26, -27, 'D', 'joao.vargas', ''),
    ('rafael', '9788508126194', -35, -21, -22, 'D', 'mariana.lopes', ''),
    ('thiago', '9788599296493', -18, -4, -2, 'D', 'joao.vargas', ''),
    ('eduardo', '9788508171279', -15, -1, -3, 'D', 'mariana.lopes', ''),

    # Ocorrências (perdido e danificado)
    ('marcelo', '9788573264463', -45, -31, None, 'P', 'joao.vargas',
     'Cliente informou que esqueceu o livro em um ônibus intermunicipal. Bloqueado até repor o exemplar.'),
    ('camila', '9788522008735', -60, -46, None, 'X', 'mariana.lopes',
     'Devolvido com várias páginas rasgadas e mancha de café na capa. Exemplar retirado do acervo.'),

    # Ativos dentro do prazo
    ('ana', '9786580309313', -5, 9, None, 'A', 'mariana.lopes', ''),
    ('lucas', '9788535914849', -3, 11, None, 'A', 'joao.vargas', ''),
    ('patricia', '9788535914849', -8, 6, None, 'A', 'mariana.lopes', ''),
    ('juliana', '9788535914849', -10, 4, None, 'A', 'joao.vargas', ''),
    ('patricia', '9788532530783', -2, 12, None, 'A', 'mariana.lopes', ''),
    ('thiago', '9788576573135', -6, 8, None, 'A', 'joao.vargas', ''),
    ('eduardo', '9788525052247', -4, 10, None, 'A', 'mariana.lopes', ''),

    # Ativos atrasados
    ('rafael', '9788535932171', -25, -11, None, 'A', 'joao.vargas', ''),
    ('camila', '9788501012074', -30, -16, None, 'A', 'mariana.lopes', ''),
    ('lucas', '9788595084742', -20, -6, None, 'A', 'joao.vargas', ''),
]

# (cliente, isbn do livro, dias da reserva, status, funcionário)
RESERVAS = [
    # Fila de espera para Grande Sertão (impede a renovação do Rafael)
    ('ana', '9788535932171', -10, 'P', 'mariana.lopes'),
    ('lucas', '9788535932171', -7, 'P', 'joao.vargas'),
    # Todos os exemplares de 1984 emprestados
    ('eduardo', '9788535914849', -2, 'P', 'mariana.lopes'),
    # O Nome do Vento foi devolvido e está separado para a Juliana
    ('juliana', '9788599296493', -12, 'D', 'joao.vargas'),
    # Reserva já atendida (virou o empréstimo ativo da Patrícia)
    ('patricia', '9788532530783', -9, 'A', 'mariana.lopes'),
    # Reserva cancelada
    ('thiago', '9788501012074', -14, 'C', 'joao.vargas'),
]


def gerar_cpf(base):
    """Gera um CPF fictício com dígitos verificadores válidos."""
    numeros = [int(d) for d in base]
    for tamanho in (9, 10):
        soma = sum(n * (tamanho + 1 - i) for i, n in enumerate(numeros[:tamanho]))
        digito = (soma * 10) % 11
        numeros.append(0 if digito == 10 else digito)
    cpf = ''.join(str(n) for n in numeros)
    return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'


class Command(BaseCommand):
    help = 'Popula o banco com livros reais (incluindo séries de fantasia), 10 clientes e cenários de empréstimos e reservas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Apaga clientes, livros, empréstimos, reservas e os funcionários de exemplo antes de popular.',
        )

    def handle(self, *args, **options):
        usuario = get_user_model()

        with transaction.atomic():
            if options['limpar']:
                Reserva.objects.all().delete()
                Emprestimo.objects.all().delete()
                Livro.objects.all().delete()
                Cliente.objects.all().delete()
                usuario.objects.filter(username__in=[f[0] for f in FUNCIONARIOS]).delete()
            elif Livro.objects.exists() or Cliente.objects.exists():
                raise CommandError('O banco já possui livros ou clientes. Use --limpar para recriar os dados.')

            hoje = timezone.localdate()
            funcionarios = self.criar_funcionarios(usuario)
            livros = self.criar_livros()
            clientes = self.criar_clientes()

            for apelido, isbn, ret, prev, dev, status, func, obs in EMPRESTIMOS:
                Emprestimo.objects.create(
                    cliente=clientes[apelido],
                    livro=livros[isbn],
                    funcionario=funcionarios[func],
                    data_retirada=hoje + timedelta(days=ret),
                    data_prevista_devolucao=hoje + timedelta(days=prev),
                    data_devolucao=hoje + timedelta(days=dev) if dev is not None else None,
                    status=status,
                    observacao=obs,
                )

            for apelido, isbn, dias, status, func in RESERVAS:
                Reserva.objects.create(
                    cliente=clientes[apelido],
                    livro=livros[isbn],
                    funcionario=funcionarios[func],
                    data_reserva=hoje + timedelta(days=dias),
                    status=status,
                )

            # Disponível = total - empréstimos ativos
            for livro in livros.values():
                ativos = livro.emprestimos.filter(status='A').count()
                livro.quantidade_disponivel = max(livro.quantidade_total - ativos, 0)
                livro.save()

        self.stdout.write(self.style.SUCCESS(
            f'Banco populado: {usuario.objects.filter(is_staff=True).count()} funcionários, '
            f'{Cliente.objects.count()} clientes, {Livro.objects.count()} livros, '
            f'{Emprestimo.objects.count()} empréstimos, {Reserva.objects.count()} reservas.'
        ))
        self.stdout.write(f'Senha dos funcionários de exemplo: {SENHA_FUNCIONARIOS}')

    def criar_funcionarios(self, usuario):
        funcionarios = {}
        for username, nome, sobrenome, ativo in FUNCIONARIOS:
            funcionario = usuario.objects.create_user(
                username=username,
                password=SENHA_FUNCIONARIOS,
                first_name=nome,
                last_name=sobrenome,
                email=f'{username}@bibliotecataquara.org.br',
                is_staff=True,
                is_active=ativo,
            )
            funcionarios[username] = funcionario
        return funcionarios

    def criar_livros(self):
        livros = {}
        for titulo, autor, editora, ano, isbn, genero, total, ativo in LIVROS:
            livros[isbn] = Livro.objects.create(
                titulo=titulo,
                autor=autor,
                editora=editora,
                ano_publicacao=ano,
                isbn=isbn,
                genero=genero,
                quantidade_total=total,
                quantidade_disponivel=total,
                ativo=ativo,
            )
        return livros

    def criar_clientes(self):
        clientes = {}
        for apelido, nome, base_cpf, telefone, endereco, ativo, bloqueado in CLIENTES:
            clientes[apelido] = Cliente.objects.create(
                nome=nome,
                cpf=gerar_cpf(base_cpf),
                telefone=telefone,
                endereco=endereco,
                ativo=ativo,
                bloqueado=bloqueado,
            )
        return clientes
