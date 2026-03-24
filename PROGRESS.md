# Assignment #2 - MCP (Model Context Protocol) - Progresso

## Estado dos Pontos do Enunciado (Parte de Treino)

| Ponto | Descrição                                      | Estado     |
|-------|-------------------------------------------------|------------|
| 1     | REST service com greet / hello world            | FEITO      |
| 2     | Entidade + Base de Dados + CRUD REST            | FEITO      |
| 3     | MCP tools a expor as mesmas operações (core partilhado) | FEITO      |
| 4     | Expor ficheiro texto/PDF como MCP resource      | FEITO      |
| 5     | Adicionar um prompt ao servidor MCP             | FEITO      |

---

## Ponto 1 - REST service com greet / hello world

### O que foi feito
Foi criado um endpoint REST `GET /` que devolve uma mensagem de saudação.

### Mecanismos e estratégias
- **Framework**: FastAPI (`main.py`)
- **Lógica partilhada**: A função `say_hello(name)` está definida em `services.py` e é reutilizada tanto pelo REST como pelo MCP (preparação para o Ponto 3).

### Código relevante

**`services.py:8-10`** - Função core:
```python
def say_hello(name: str = "World") -> str:
    return f"Hello, {name}!"
```

**`main.py:27-29`** - Endpoint REST:
```python
@app.get("/")
async def root(name: str = "World") -> dict:
    return {"message": say_hello(name)}
```

O endpoint aceita um query parameter `name` opcional (default: `"World"`) e devolve JSON com a mensagem.

---

## Ponto 2 - Entidade + Base de Dados + CRUD REST

### O que foi feito
Foi criada a entidade `Item` ligada a uma base de dados PostgreSQL, com operações CRUD completas expostas via REST.

### Mecanismos e estratégias
- **ORM**: SQLModel (combina SQLAlchemy + Pydantic) para definir modelos que servem simultaneamente como schema de BD e de validação de dados.
- **Base de dados**: PostgreSQL, configurada via variável de ambiente `DATABASE_URL` no ficheiro `.env`.
- **Padrão de modelos**: Separação em `ItemBase` (campos comuns), `Item` (tabela BD), `ItemCreate` (criação), `ItemUpdate` (atualização parcial) — segue as boas práticas do SQLModel.
- **Dependency Injection**: O FastAPI injeta a sessão de BD via `Depends(get_session)`.

### Código relevante

**`models.py`** - Definição da entidade:
```python
class ItemBase(SQLModel):
    name: str = Field(index=True)
    description: str | None = None
    price: float = Field(ge=0)
    quantity: int = Field(default=0, ge=0)

class Item(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class ItemCreate(ItemBase):
    pass

class ItemUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=0)
```

- `ItemBase`: Classe base com os campos partilhados e validações (`ge=0` para preço e quantidade).
- `Item`: Modelo de tabela com `id` auto-gerado.
- `ItemCreate`: Herda de `ItemBase`, exige todos os campos obrigatórios.
- `ItemUpdate`: Todos os campos opcionais, para permitir atualizações parciais (PATCH).

**`database.py`** - Configuração da BD:
```python
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

- Usa `dotenv` para carregar a `DATABASE_URL` do ficheiro `.env`.
- `create_db_and_tables()` cria as tabelas automaticamente ao iniciar a app.
- `get_session()` é um generator usado como dependência do FastAPI.

**`services.py`** - Lógica CRUD (funções core partilhadas):
```python
def create_item(session, item_data)  # Cria item na BD
def get_item(session, item_id)       # Busca item por ID
def get_items(session, offset, limit) # Lista items com paginação
def update_item(session, item_id, item_data)  # Atualização parcial
def delete_item(session, item_id)    # Apaga item, retorna bool
```

**`main.py`** - Endpoints REST:
| Método | Rota              | Descrição              | Status Code |
|--------|-------------------|------------------------|-------------|
| POST   | `/items`          | Criar item             | 201         |
| GET    | `/items`          | Listar items           | 200         |
| GET    | `/items/{item_id}`| Obter item por ID      | 200         |
| PATCH  | `/items/{item_id}`| Atualizar item parcial | 200         |
| DELETE | `/items/{item_id}`| Apagar item            | 204         |

### Inicialização
A criação de tabelas acontece no `lifespan` do FastAPI (`main.py:18-21`):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
```

---

## Ponto 3 - MCP tools a expor as mesmas operações

### O que foi feito
Foi criado um servidor MCP (`mcp_server.py`) que expõe as mesmas operações CRUD como MCP tools. O ponto-chave é que **as funções core em `services.py` são partilhadas** entre REST e MCP, conforme a Figura 1 do enunciado.

### Mecanismos e estratégias
- **Framework MCP**: FastMCP (biblioteca `mcp` para Python).
- **Arquitetura partilhada**: As tools MCP chamam as mesmas funções de `services.py` que os endpoints REST. Isto garante que a lógica de negócio é implementada uma única vez.
- **Gestão de sessão**: No MCP, a sessão é criada manualmente com `with Session(engine)`, ao contrário do REST que usa Dependency Injection do FastAPI.

### Código relevante

**`mcp_server.py`** - Servidor MCP com tools:

| Tool MCP        | Função core chamada | Descrição                  |
|-----------------|---------------------|----------------------------|
| `hello`         | `say_hello()`       | Saudação                   |
| `add_item`      | `create_item()`     | Criar item                 |
| `list_all_items`| `get_items()`       | Listar todos os items      |
| `read_item`     | `get_item()`        | Obter item por ID          |
| `modify_item`   | `update_item()`     | Atualizar item             |
| `remove_item`   | `delete_item()`     | Apagar item                |

Exemplo de uma tool MCP (`mcp_server.py:26-33`):
```python
@mcp.tool()
def add_item(name: str, price: float, description: str = "", quantity: int = 0) -> str:
    """Create a new item."""
    with Session(engine) as session:
        item = create_item(
            session, ItemCreate(name=name, price=price, description=description, quantity=quantity)
        )
        return f"Created item {item.id}: {item.name}"
```

### Arquitetura (conforme Figura 1 do enunciado)
```
┌─────────┐     ┌──────────────┐     ┌──────────┐
│  REST   │────>│   Core       │<────│   MCP    │
│ (FastAPI)│     │ (services.py)│     │ (FastMCP)│
└─────────┘     └──────┬───────┘     └──────────┘
                       │
                ┌──────▼───────┐
                │  Database    │
                │ (PostgreSQL) │
                └──────────────┘
```

---

## Ponto 4 - Expor ficheiro texto/PDF como MCP resource

### O que foi feito
Foram criados dois ficheiros de texto e expostos como MCP resources no servidor MCP. Um agente AI pode consultar estes recursos para obter contexto sobre o sistema sem executar nenhuma ação.

### Diferença entre Tools e Resources
- **Tools** = ações que o agente executa (criar, ler, apagar items)
- **Resources** = informação/contexto que o agente pode consultar (read-only)

### Mecanismos e estratégias
- **Decorator `@mcp.resource()`**: Regista uma função como recurso MCP com um URI único.
- **URI scheme `resource://`**: Cada recurso tem um identificador único que o agente usa para o consultar.
- **Leitura de ficheiros com `pathlib.Path`**: Os ficheiros `.txt` são lidos de forma robusta usando `Path.read_text()` com encoding UTF-8.
- **`BASE_DIR`**: Usa `Path(__file__).parent` para garantir que os ficheiros são encontrados independentemente do diretório de trabalho.

### Ficheiros criados

**`db_model.txt`** - Documentação do modelo da base de dados:
- Descreve a tabela `item` com todas as colunas, tipos e restrições.
- Inclui notas sobre auto-criação de tabelas e validação ao nível da aplicação.

**`internal_report.txt`** - Relatório interno do sistema:
- Visão geral do sistema e arquitetura.
- Lista de endpoints REST disponíveis.
- Lista de MCP tools e resources disponíveis.
- Stack tecnológica utilizada.

### Código relevante

**`mcp_server.py`** - Resources MCP:
```python
BASE_DIR = Path(__file__).parent

@mcp.resource("resource://db-model")
def get_db_model() -> str:
    """Returns the database model documentation describing all tables and columns."""
    return (BASE_DIR / "db_model.txt").read_text(encoding="utf-8")

@mcp.resource("resource://internal-report")
def get_internal_report() -> str:
    """Returns an internal report with system overview, endpoints, and architecture."""
    return (BASE_DIR / "internal_report.txt").read_text(encoding="utf-8")
```

### Resources disponíveis

| URI                        | Ficheiro              | Descrição                          |
|----------------------------|-----------------------|------------------------------------|
| `resource://db-model`      | `db_model.txt`        | Modelo da base de dados            |
| `resource://internal-report`| `internal_report.txt`| Relatório interno do sistema       |

---

## Ponto 5 - Adicionar prompt ao servidor MCP

### O que foi feito
Foi criado um MCP prompt chamado `inventory_report` que fornece ao agente AI um template de instruções para gerar um relatório de inventário completo.

### Diferença entre Tools, Resources e Prompts
- **Tools** = ações que o agente executa (CRUD)
- **Resources** = informação/contexto read-only
- **Prompts** = templates de instruções reutilizáveis que guiam o agente numa tarefa complexa

### Mecanismos e estratégias
- **Decorator `@mcp.prompt()`**: Regista uma função como prompt template no servidor MCP.
- **Parâmetro `sort_by`**: Permite ao utilizador escolher o critério de ordenação (name, price, quantity), tornando o prompt flexível e reutilizável.
- **Instruções estruturadas**: O prompt diz ao agente exatamente que tools usar (`list_all_items`) e como formatar o resultado (tabela, resumo com totais, item mais caro, item com menor stock).

### Código relevante

**`mcp_server.py`** - Prompt MCP:
```python
@mcp.prompt()
def inventory_report(sort_by: str = "name") -> str:
    """Generate an inventory report sorted by a given criterion (name, price, or quantity)."""
    return (
        f"Use the 'list_all_items' tool to retrieve every item in the database. "
        f"Then organize the results into a well-formatted inventory report sorted by {sort_by}. "
        f"The report should include:\n"
        f"1. A header with the report title and the current date.\n"
        f"2. A table or list of all items showing: ID, Name, Description, Price, and Quantity.\n"
        f"3. A summary section at the end with:\n"
        f"   - Total number of items\n"
        f"   - Total inventory value (sum of price * quantity for each item)\n"
        f"   - Item with the highest price\n"
        f"   - Item with the lowest stock (quantity)\n"
        f"Sort all items by '{sort_by}' in ascending order."
    )
```

### Como funciona na prática
1. O agente AI (ex: VS Code com MCP client) vê o prompt `inventory_report` na lista de prompts disponíveis.
2. O utilizador seleciona o prompt e opcionalmente escolhe `sort_by` (default: `"name"`).
3. O agente recebe as instruções formatadas e usa a tool `list_all_items` para obter os dados.
4. O agente organiza os dados conforme as instruções e apresenta o relatório ao utilizador.

---

## Fase 1 (Avaliação) - Adicionar 2ª entidade: Supplier

### O que foi feito
Foi adicionada a entidade `Supplier` (Fornecedor) com relação 1:N com `Item` — um Supplier fornece vários Items, cada Item pode pertencer a um Supplier. CRUD completo exposto via REST e MCP, com core functions partilhadas.

### Modelo Supplier

**`models.py`** — Novos modelos:
```python
class SupplierBase(SQLModel):
    name: str = Field(index=True)
    contact: str | None = None
    email: str | None = None

class Supplier(SupplierBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    items: list["Item"] = Relationship(back_populates="supplier")
```

**Relação com Item** — `Item` ganhou:
```python
supplier_id: int | None = Field(default=None, foreign_key="supplier.id")
supplier: Supplier | None = Relationship(back_populates="items")
```

### Core functions (services.py)

| Função               | Descrição                      |
|----------------------|--------------------------------|
| `create_supplier()`  | Criar supplier na BD           |
| `get_supplier()`     | Buscar supplier por ID         |
| `get_suppliers()`    | Listar suppliers com paginação |
| `update_supplier()`  | Atualização parcial            |
| `delete_supplier()`  | Apagar supplier                |

### Endpoints REST (main.py)

| Método | Rota                       | Descrição                 | Status Code |
|--------|----------------------------|---------------------------|-------------|
| POST   | `/suppliers`               | Criar supplier            | 201         |
| GET    | `/suppliers`               | Listar suppliers          | 200         |
| GET    | `/suppliers/{supplier_id}` | Obter supplier por ID     | 200         |
| PATCH  | `/suppliers/{supplier_id}` | Atualizar supplier parcial| 200         |
| DELETE | `/suppliers/{supplier_id}` | Apagar supplier           | 204         |

### MCP Tools (mcp_server.py)

| Tool MCP             | Função core chamada    | Descrição              |
|----------------------|------------------------|------------------------|
| `add_supplier`       | `create_supplier()`    | Criar supplier         |
| `list_all_suppliers` | `get_suppliers()`      | Listar suppliers       |
| `read_supplier_tool` | `get_supplier()`       | Obter supplier por ID  |
| `modify_supplier`    | `update_supplier()`    | Atualizar supplier     |
| `remove_supplier`    | `delete_supplier()`    | Apagar supplier        |

### Arquitetura atualizada
```
┌─────────┐     ┌──────────────┐     ┌──────────┐
│  REST   │────>│   Core       │<────│   MCP    │
│ (FastAPI)│     │ (services.py)│     │ (FastMCP)│
└─────────┘     └──────┬───────┘     └──────────┘
                       │
                ┌──────▼───────┐
                │  Database    │
                │ (PostgreSQL) │
                │              │
                │ ┌──────────┐ │
                │ │ supplier │ │
                │ └────┬─────┘ │
                │      │ 1:N   │
                │ ┌────▼─────┐ │
                │ │   item   │ │
                │ └──────────┘ │
                └──────────────┘
```

### Nota sobre migração
Como a tabela `item` já existia, é necessário adicionar a coluna `supplier_id` manualmente:
```sql
ALTER TABLE item ADD COLUMN supplier_id INTEGER REFERENCES supplier(id);
```
Ou alternativamente, apagar as tabelas e deixar o sistema recriá-las automaticamente.

---

## Como executar

### Servidor REST (FastAPI)
```bash
uv run python main.py
# ou
uv run uvicorn main:app --reload --port 8000
```

### Servidor MCP
```bash
uv run python mcp_server.py
```

### Configuração
Criar ficheiro `.env` com:
```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

## Dependências principais
- **FastAPI** - Framework REST
- **SQLModel** - ORM (SQLAlchemy + Pydantic)
- **FastMCP** (pacote `mcp`) - Framework MCP
- **psycopg2-binary** - Driver PostgreSQL
- **uvicorn** - Servidor ASGI
