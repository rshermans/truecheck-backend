# TrueCheck Backend API

Backend FastAPI para a aplicação TrueCheck de verificação de factualidade.

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.11+
- pip ou virtualenv

### Instalação

1. **Criar ambiente virtual:**
```bash
python -m venv venv
```

2. **Ativar ambiente virtual:**

**Windows:**
```bash
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

3. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

4. **Configurar variáveis de ambiente:**
```bash
# Copiar o arquivo de exemplo
copy .env.example .env

# Editar .env com suas chaves de API (já configurado)
```

### Executar o Servidor

```bash
# Modo desenvolvimento (com auto-reload)
python main.py

# Ou usando uvicorn diretamente
uvicorn main:app --reload --port 5000
```

O servidor estará disponível em: **http://localhost:5000**

## 📚 Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc
- **Health Check:** http://localhost:5000/api/health

## 🔌 Endpoints

### Análise Preliminar
`POST /api/analysis/preliminary`

Realiza análise inicial do conteúdo com IA.

**Request:**
```json
{
  "type": "text",
  "content": "Texto para analisar..."
}
```

### Verificação Cruzada
`POST /api/analysis/cross-verification`

Verifica conteúdo contra bases de fact-checking.

### Análise de Contexto
`POST /api/analysis/context`

Analisa contexto e sentimento do conteúdo.

### Avaliação Final
`POST /api/analysis/final`

Compara avaliação do usuário com análise da IA.

## 🔑 Configuração de API Keys

As seguintes chaves de API estão configuradas no arquivo `.env`:

- **OpenAI API:** Para análise de conteúdo com GPT-4
- **Google Fact Check API:** Para verificação cruzada

## 🛠️ Tecnologias

- **FastAPI** - Framework web moderno e rápido
- **OpenAI GPT-4** - Análise de conteúdo com IA
- **Google Fact Check API** - Verificação de fatos
- **Pydantic** - Validação de dados
- **Uvicorn** - Servidor ASGI

## 📁 Estrutura do Projeto

```
backend/
├── main.py                 # Aplicação principal
├── config.py              # Configurações
├── requirements.txt       # Dependências
├── .env                   # Variáveis de ambiente
├── models/
│   └── schemas.py        # Modelos Pydantic
├── routes/
│   └── analysis.py       # Rotas da API
└── services/
    ├── ai_analyzer.py    # Serviço de análise IA
    ├── fact_checker.py   # Serviço de fact-checking
    └── context_analyzer.py # Serviço de análise de contexto
```

## 🔒 Segurança

- CORS configurado para permitir apenas origens específicas
- Chaves de API armazenadas em variáveis de ambiente
- Validação de dados com Pydantic
- Tratamento de erros robusto

## 🧪 Testes

Para testar os endpoints, você pode usar:

1. **Swagger UI** (recomendado): http://localhost:5000/docs
2. **curl** ou **Postman**
3. **Frontend TrueCheck**

## 📝 Notas

- O backend está configurado para funcionar com o frontend em `http://localhost:5173`
- Logs de erro são exibidos no console para debugging
- Em caso de falha das APIs externas, o sistema retorna dados simulados

## 🎮 Sistema de Gamificação

### Visão Geral
O TrueCheck inclui um sistema de gamificação que recompensa os alunos por completarem análises de conteúdo, incentivando o aprendizado contínuo.

### Níveis e XP
- **Níveis:** 1-10 com progressão exponencial
- **XP Base:** +10 XP por análise completa
- **Bônus de Precisão:**
  - Discrepância ≤10: +5 XP (excelente)
  - Discrepância 11-25: +2 XP (bom)
  - Discrepância >25: +0 XP (precisa melhorar)

### Tabela de Níveis
| Nível | XP Necessário |
|-------|---------------|
| 1     | 0-99          |
| 2     | 100-249       |
| 3     | 250-499       |
| 4     | 500-849       |
| 5     | 850-1299      |
| 6     | 1300-1849     |
| 7     | 1850-2499     |
| 8     | 2500-3249     |
| 9     | 3250-4099     |
| 10    | 4100+         |

### Endpoints de Perfil

**GET /api/student/profile** (Autenticado)
```json
{
  "username": "aluno123",
  "level": 3,
  "xp": 350,
  "xp_progress": {
    "current": 100,
    "needed": 250
  },
  "total_analyses": 15,
  "avg_accuracy": 85.5
}
```

**GET /api/student/stats** (Autenticado)
```json
{
  "recent_analyses": [...],
  "total_xp": 350,
  "current_level": 3
}
```

### Testes
Execute os testes unitários do sistema de gamificação:
```bash
pytest test_gamification.py -v
```
