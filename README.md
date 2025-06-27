# CodePlan: Gerenciamento Inteligente de Tarefas com IA

CodePlan é uma plataforma para ajudar times de desenvolvimento a gerenciar tarefas de forma inteligente, utilizando Inteligência Artificial para organizar, priorizar e sugerir melhores práticas para atividades extraídas diretamente do Trello e Jira.

## Funcionalidades Principais

- **Integração direta com Trello e Jira:** Conecte suas contas e importe automaticamente suas tarefas.
- **IA para priorização e organização:** A IA analisa suas tarefas e sugere uma ordem estratégica baseada em critérios como urgência, impacto, dependências e melhores práticas ágeis.
- **Assistente para desenvolvedores:** Para tarefas técnicas, a IA recomenda bibliotecas, frameworks, próximos passos, riscos e dicas práticas para acelerar a conclusão.
- **Fluxo de autenticação seguro:** Login próprio e autenticação OAuth com Jira e Trello.

## Tecnologias Utilizadas

- **Backend:** Django, Django REST Framework, Python
- **Frontend:** React, JavaScript

## Como rodar localmente

1. **Clone o repositório**
2. **Backend**
   - Instale as dependências:
     ```sh
     pip install -r backend/requirements.txt
     ```
   - Configure as variáveis de ambiente em `.env` (veja exemplos em `backend/`).
   - Inicie o backend:
     ```sh
     cd backend
     python manage.py runserver
     ```
   - Ou utilize Docker:
     ```sh
     cd backend
     docker-compose up
     ```
3. **Frontend**
   - Instale as dependências:
     ```sh
     cd frontend
     npm install
     ```
   - Inicie o frontend:
     ```sh
     npm start
     ```

## Como usar

1. Acesse `/users/login` ou `/users/register` para criar sua conta e autenticar-se.
2. Escolha integrar com Jira `/jira/login` ou Trello `/trello/login` via OAuth.
3. Após autenticação, suas tarefas serão importadas e organizadas automaticamente pela IA.
4. Visualize sugestões de priorização, organização e dicas técnicas para cada tarefa.

## Público-alvo

Desenvolvedores, Scrum Masters, Product Owners e times ágeis que utilizam Jira ou Trello e desejam potencializar a produtividade com IA.

---
