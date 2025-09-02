# SaaS de Agendamento de Serviços - Backend e Painel de Admin

Este é o backend completo e o painel de administração para uma aplicação SaaS (Software as a Service) de agendamento de serviços, construída com Python, Flask e SQLite.

O sistema possui três componentes principais:
1.  Uma **API RESTful** para interações programáticas (ex: para um app mobile ou frontend customizado).
2.  Um **Painel de Administração** para proprietários de lojas gerenciarem seus negócios.
3.  Um **Painel do Profissional** para os profissionais verem seus agendamentos e comissões.

## Instalação

Siga os passos abaixo para configurar e executar o ambiente de desenvolvimento local.

### Pré-requisitos

- Python 3.8+
- `pip` e `venv` (módulo de ambientes virtuais do Python)

### Passos

1.  **Clone o repositório (ou use os arquivos existentes):**
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd <NOME_DO_DIRETORIO>
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Criar o ambiente
    python -m venv venv
    # Ativar no Linux/macOS
    source venv/bin/activate
    # Ativar no Windows (PowerShell)
    # .\venv\Scripts\Activate.ps1
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure o Banco de Dados:**
    Execute as migrações para criar o arquivo `site.db` e todas as tabelas.
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
    A API e as páginas web estarão em execução e disponíveis em `http://127.0.0.1:5000`.

## Uso da Plataforma

A plataforma possui 3 pontos de entrada principais.

### 1. Página Principal (Login / Cadastro)

-   **URL:** `/`
-   **Descrição:** Página principal onde todos os usuários (Proprietários e Profissionais) podem fazer login. Novos Proprietários também podem se cadastrar aqui.
-   **Funcionalidades:**
    -   Alternar entre os formulários de Login e Cadastro.
    -   No login, selecionar o tipo de usuário (Proprietário ou Profissional).

### 2. Painel de Administração do Proprietário

-   **URL:** `/admin/dashboard` (requer login de proprietário)
-   **Descrição:** O painel central para o proprietário gerenciar todos os aspectos de seus negócios.
-   **Funcionalidades:**
    -   Visualizar e criar múltiplas lojas.
    -   Para cada loja, acessar um painel de gerenciamento detalhado.
    -   **Gerenciamento da Loja:**
        -   Adicionar, editar e remover **Serviços**, incluindo a configuração de cobrança de **sinal**.
        -   Adicionar, editar e remover **Profissionais**, definindo suas credenciais de login, telefone e **percentual de comissão**.
        -   Visualizar todos os **Agendamentos**.
        -   Alterar o status dos agendamentos (confirmar, cancelar, etc.).
        -   Marcar a **comissão** de um agendamento concluído como paga.
        -   Definir configurações da loja, como a **Chave PIX** e a **URL do Webhook**.

### 3. Painel do Profissional

-   **URL:** `/pro/dashboard` (requer login de profissional)
-   **Descrição:** Um dashboard para o profissional acompanhar seu trabalho e ganhos.
-   **Funcionalidades:**
    -   Visualizar agendamentos separados por status: Próximos, Realizados e Cancelados.
    -   Acompanhar o status das comissões (Pendentes e Pagas).

## Uso da API

A API pública continua disponível para integrações. As rotas são prefixadas pelo `path` da loja (ex: `/minha-loja/servicos`).

#### Listar Serviços
- **Endpoint:** `GET /<loja_path>/servicos`
- **Descrição:** Retorna a lista de todos os serviços oferecidos pela loja.

#### Listar Profissionais por Serviço
- **Endpoint:** `GET /<loja_path>/servicos/profissionais?servico_id=<id>`
- **Descrição:** Retorna os profissionais que realizam um serviço específico.

#### Listar Horários Disponíveis
- **Endpoint:** `GET /<loja_path>/horarios-disponiveis?servico_id=<id>&profissional_id=<id>&data=<YYYY-MM-DD>`
- **Descrição:** Calcula e retorna os horários disponíveis.

#### Criar um Agendamento
- **Endpoint:** `POST /<loja_path>/agendamentos`
- **Descrição:** Cria um novo agendamento. Se o serviço exigir sinal, a resposta incluirá um `link_pagamento`.
- **Corpo (JSON):** `{ "servico_id": 1, "profissional_id": 1, ... }`

#### Atualizar Status do Agendamento
- **Endpoint:** `PATCH /<loja_path>/agendamentos/<id>/status`
- **Descrição:** Atualiza o status de um agendamento.
- **Corpo (JSON):** `{ "status": "confirmado" }`
