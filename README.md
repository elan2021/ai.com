# SaaS de Agendamento de Serviços

Este é o backend para uma aplicação SaaS (Software as a Service) de agendamento de serviços, construída com Python, Flask e SQLite. A API permite que proprietários de negócios se cadastrem, criem suas próprias lojas com um URL exclusivo e gerenciem agendamentos.

## Instalação

Siga os passos abaixo para configurar e executar o ambiente de desenvolvimento local.

### Pré-requisitos

- Python 3.8+
- `pip` e `venv` (módulo de ambientes virtuais do Python)

### Passos

1.  **Clone o repositório (ou use os arquivos existentes):**
    Se você estiver configurando de um repositório git, clone-o.
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd <NOME_DO_DIRETORIO>
    ```

2.  **Crie e ative um ambiente virtual:**
    É uma boa prática isolar as dependências do projeto.
    ```bash
    # Criar o ambiente
    python -m venv venv
    # Ativar no Linux/macOS
    source venv/bin/activate
    # Ativar no Windows (PowerShell)
    # .\venv\Scripts\Activate.ps1
    ```

3.  **Instale as dependências:**
    O arquivo `requirements.txt` contém todas as bibliotecas necessárias.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure o Banco de Dados:**
    Execute a migração inicial para criar o arquivo `site.db` e todas as tabelas.
    ```bash
    # Para Linux/macOS
    export FLASK_APP=run.py
    # Para Windows
    # set FLASK_APP=run.py

    # Executar o comando de upgrade
    flask db upgrade
    ```
    Isso criará o banco de dados dentro de uma nova pasta `instance/`.

5.  **Execute a Aplicação:**
    ```bash
    flask run
    ```
    A API estará em execução e disponível em `http://127.0.0.1:5000`.

## Uso da API

A seguir, a documentação de todos os endpoints disponíveis.

---

### Autenticação

#### 1. Registrar um Novo Proprietário

- **Endpoint:** `POST /auth/register`
- **Descrição:** Cria uma nova conta de proprietário para usar o sistema.
- **Corpo da Requisição (JSON):**
  ```json
  {
      "nome": "Nome do Proprietário",
      "telefone": "11999998888",
      "username": "proprietario_user",
      "password": "senha_segura_123"
  }
  ```
- **Resposta de Sucesso (201):**
  ```json
  {
      "message": "Proprietário registrado com sucesso!"
  }
  ```

#### 2. Fazer Login

- **Endpoint:** `POST /auth/login`
- **Descrição:** Autentica um proprietário e retorna um token JWT para ser usado em rotas protegidas.
- **Corpo da Requisição (JSON):**
  ```json
  {
      "username": "proprietario_user",
      "password": "senha_segura_123"
  }
  ```
- **Resposta de Sucesso (200):**
  ```json
  {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwcm9..."
  }
  ```

---

### Gestão de Lojas

#### 1. Criar uma Nova Loja

- **Endpoint:** `POST /lojas/`
- **Autenticação:** **Requerida**. Envie o token JWT no cabeçalho `Authorization`.
  - **Exemplo:** `Authorization: Bearer <seu_token_jwt>`
- **Descrição:** Cria uma nova loja (subsite) associada ao proprietário autenticado. O `path` deve ser único.
- **Corpo da Requisição (JSON):**
  ```json
  {
      "path": "minha-barbearia",
      "title": "Barbearia do Zé"
  }
  ```
- **Resposta de Sucesso (201):**
  ```json
  {
      "message": "Loja criada com sucesso!",
      "loja": {
          "id": 1,
          "path": "minha-barbearia",
          "title": "Barbearia do Zé"
      }
  }
  ```

---

### API Pública da Loja

Todos os endpoints a seguir são prefixados com o `path` da loja. Por exemplo, se o `path` da sua loja é `minha-barbearia`, o endpoint para listar serviços será `/minha-barbearia/servicos`.

#### 1. Listar Serviços da Loja

- **Endpoint:** `GET /<loja_path>/servicos`
- **Descrição:** Retorna a lista de todos os serviços oferecidos pela loja.
- **Resposta de Sucesso (200):**
  ```json
  [
      {
          "id": 1,
          "nome": "Corte de Cabelo",
          "preco": "50.00",
          "duracao": 45,
          "profissionais": [
              {
                  "id": 1,
                  "nome": "João Cabeleireiro"
              }
          ]
      }
  ]
  ```

#### 2. Listar Profissionais por Serviço

- **Endpoint:** `GET /<loja_path>/servicos/profissionais?servico_id=<id>`
- **Descrição:** Retorna os profissionais que realizam um serviço específico.
- **Exemplo de URL:** `GET /minha-barbearia/servicos/profissionais?servico_id=1`
- **Resposta de Sucesso (200):**
  ```json
  [
      {
          "id": 1,
          "nome": "João Cabeleireiro"
      }
  ]
  ```

#### 3. Listar Horários Disponíveis

- **Endpoint:** `GET /<loja_path>/horarios-disponiveis?servico_id=<id>&profissional_id=<id>&data=<YYYY-MM-DD>`
- **Descrição:** Calcula e retorna os horários disponíveis para um serviço, profissional e data.
- **Exemplo de URL:** `GET /minha-barbearia/horarios-disponiveis?servico_id=1&profissional_id=1&data=2025-12-25`
- **Resposta de Sucesso (200):**
  ```json
  [
      {
          "value": "09:00",
          "label": "09:00 - 09:45"
      },
      {
          "value": "10:00",
          "label": "10:00 - 10:45"
      }
  ]
  ```

#### 4. Criar um Agendamento

- **Endpoint:** `POST /<loja_path>/agendamentos`
- **Descrição:** Cria um novo agendamento.
- **Corpo da Requisição (JSON):**
  ```json
  {
      "servico_id": 1,
      "profissional_id": 1,
      "data_agendamento": "2025-12-25",
      "horario_inicio": "10:00",
      "cliente_nome": "Fulano de Tal",
      "cliente_telefone": "5511987654321",
      "cliente_email": "fulano@email.com"
  }
  ```
- **Resposta de Sucesso (201):**
  ```json
  {
      "message": "Agendamento criado com sucesso!",
      "agendamento_id": 123
  }
  ```

#### 5. Atualizar Status do Agendamento

- **Endpoint:** `PATCH /<loja_path>/agendamentos/<id>/status`
- **Descrição:** Atualiza o status de um agendamento.
- **Corpo da Requisição (JSON):**
  ```json
  {
      "status": "confirmado"
  }
  ```
- **Resposta de Sucesso (200):**
  ```json
  {
      "message": "Status do agendamento atualizado com sucesso!",
      "agendamento_id": 123,
      "novo_status": "confirmado"
  }
  ```
