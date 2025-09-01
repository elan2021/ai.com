from .db import db
import datetime

# Tabela de associação para o relacionamento muitos-para-muitos
# entre Servico e Profissional.
servicos_profissionais = db.Table('servicos_profissionais',
    db.Column('servico_id', db.Integer, db.ForeignKey('servico.id'), primary_key=True),
    db.Column('profissional_id', db.Integer, db.ForeignKey('profissional.id'), primary_key=True)
)

class Proprietario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    lojas = db.relationship('Loja', backref='proprietario', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Proprietario {self.username}>'

class Loja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    proprietario_id = db.Column(db.Integer, db.ForeignKey('proprietario.id'), nullable=False)

    servicos = db.relationship('Servico', backref='loja', lazy=True, cascade="all, delete-orphan")
    profissionais = db.relationship('Profissional', backref='loja', lazy=True, cascade="all, delete-orphan")
    agendamentos = db.relationship('Agendamento', backref='loja', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Loja {self.title}>'

class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    duracao = db.Column(db.Integer, nullable=False)  # Duração em minutos
    loja_id = db.Column(db.Integer, db.ForeignKey('loja.id'), nullable=False)

    profissionais = db.relationship('Profissional', secondary=servicos_profissionais,
                                    lazy='subquery', backref=db.backref('servicos', lazy=True))

    def __repr__(self):
        return f'<Servico {self.nome}>'

class Profissional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True) # Temporariamente nulo para migração
    password_hash = db.Column(db.String(128), nullable=True) # Temporariamente nulo para migração
    commission_percentage = db.Column(db.Numeric(5, 2), nullable=False, default=0.0)
    loja_id = db.Column(db.Integer, db.ForeignKey('loja.id'), nullable=False)

    agendamentos = db.relationship('Agendamento', backref='profissional', lazy=True)
    horarios_trabalho = db.relationship('HorarioTrabalho', backref='profissional', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Profissional {self.nome}>'

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_agendamento = db.Column(db.Date, nullable=False)
    horario_inicio = db.Column(db.Time, nullable=False)
    horario_fim = db.Column(db.Time, nullable=False)
    cliente_nome = db.Column(db.String(100), nullable=False)
    cliente_telefone = db.Column(db.String(20), nullable=False)
    cliente_email = db.Column(db.String(120))
    observacoes_cliente = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default='pendente')
    commission_paid = db.Column(db.Boolean, default=False, nullable=False)

    loja_id = db.Column(db.Integer, db.ForeignKey('loja.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)

    servico = db.relationship('Servico')

    def __repr__(self):
        return f'<Agendamento {self.id} em {self.data_agendamento} às {self.horario_inicio}>'

class HorarioTrabalho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'), nullable=False)
    dia_da_semana = db.Column(db.Integer, nullable=False) # 0=Segunda, 1=Terça, ..., 6=Domingo
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f'<HorarioTrabalho {self.profissional.nome} - Dia {self.dia_da_semana}>'
