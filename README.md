# 🤖 MCP Business Automation Agent

Een geavanceerde AI-agent voor bedrijfsautomatisering die integreert met MCP (Model Context Protocol) servers voor uitgebreide database-analyse, e-mailcommunicatie, webonderzoek en strategische besluitvorming.

Built met **PydanticAI** voor robuuste agent architectuur, type veiligheid en productie-gereed ontwerp.

## 🚀 Overzicht

De **MCP Business Automation Agent** is een conversational AI-systeem dat sophisticate bedrijfsworkflows kan uitvoeren door je bestaande MCP server tools te orchestreren. Het project bevat zowel een **production-ready agent** als uitgebreide **learning resources** voor PydanticAI ontwikkeling.

### 🎯 Hoofdcomponenten

- **🤖 CLI Agent** (`mcp_business_agent/`) - Production-ready business automation agent
- **🌐 Web Interface** (`frontend/`) - Modern Streamlit + FastAPI web interface  
- **📚 Learning Examples** (`examples/`) - Uitgebreide PydanticAI voorbeelden en patronen
- **🔬 PRP System** (`PRPs/`) - PydanticAI Research Pattern methodology

### ✨ Kernfunctionaliteiten

- **15+ MCP Tools** voor database, email, web research en thinking
- **Multi-provider LLM ondersteuning** (OpenAI + Anthropic fallback)
- **Modern web interface** met real-time streaming en chat history
- **Robuuste foutafhandeling** met retry logica en rate limiting  
- **Permission-based access control** met security validatie
- **Dual interface** - CLI én web-based interaction
- **Comprehensive testing** met TestModel patronen
- **Learning resources** - Complete PydanticAI development examples

## 🏗️ Architectuur

### Project Structure
```
my-first-agent/
├── mcp_business_agent/      # 🤖 Production Agent
│   ├── agent.py            # Hoofd agent met 15+ MCP tools
│   ├── cli.py              # Interactieve CLI interface
│   ├── mcp_client.py       # Robuuste MCP server communicatie
│   ├── auth_manager.py     # GitHub OAuth token management
│   ├── settings.py         # Environment-based configuratie
│   ├── providers.py        # Multi-provider LLM ondersteuning
│   ├── models.py           # Pydantic data modellen
│   ├── workflow_manager.py # Multi-step automatisering
│   ├── dependencies.py     # Dependency injection systeem
│   ├── requirements.txt    # Dependencies
│   └── tests/              # Uitgebreide test suite
├── frontend/               # 🌐 Web Interface  
│   ├── streamlit_app.py    # Modern chat interface
│   ├── fastapi_server.py   # REST API backend
│   ├── start_servers.py    # Development startup script
│   └── requirements.txt    # Frontend dependencies
├── examples/               # 📚 Learning Resources
│   ├── basic_chat_agent/   # Simple conversational patterns
│   ├── tool_enabled_agent/ # Custom tool implementations
│   ├── structured_output_agent/ # Pydantic model outputs
│   ├── main_agent_reference/    # Complete reference implementation
│   └── testing_examples/   # Test patterns and validation
├── PRPs/                   # 🔬 Research Patterns
│   ├── INITIAL.md          # Agent requirement templates
│   └── *.md               # Generated PRP documents
└── CLAUDE.md              # Global PydanticAI development rules
```

## 🛠️ Setup & Installatie

### 1. Installeer Dependencies

#### Agent Dependencies
```bash
# Installeer Python dependencies voor de agent
pip install -r mcp_business_agent/requirements.txt

# Of gebruik een virtual environment (aanbevolen)
python -m venv venv
source venv/bin/activate  # Linux/Mac  
# venv\Scripts\activate   # Windows
pip install -r mcp_business_agent/requirements.txt
```

#### Frontend Dependencies (Optioneel)
```bash
# Voor de web interface
pip install -r frontend/requirements.txt
```

### 2. Configureer Environment

Kopieer het environment template en vul je configuratie in:

```bash
cp mcp_business_agent/.env.example .env
```

Vul de volgende vereiste velden in `.env`:

```bash
# MCP Server Configuration
MCP_SERVER_URL=https://your-mcp-server.workers.dev
GITHUB_ACCESS_TOKEN=ghp_your_github_oauth_token_here

# LLM Configuration  
LLM_API_KEY=sk-your-openai-api-key-here
LLM_MODEL=gpt-4o

# Optional Anthropic Fallback
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
```

**GitHub OAuth Setup:**

Voor GitHub OAuth functionaliteit, gebruik de ingebouwde setup utility:

```bash
python -m mcp_business_agent.auth_cli
```

Dit helpt je met het configureren van OAuth tokens voor GitHub integratie.

### 3. Valideer Setup

```bash
# Test configuratie
python -m mcp_business_agent --validate-only

# Toon systeem status
python -m mcp_business_agent --status
```

## 🎯 Gebruik

### 🤖 CLI Interface

Start de conversational command-line interface:

```bash
python -m mcp_business_agent
```

Of met debug mode:

```bash
python -m mcp_business_agent --debug
```

### 🌐 Web Interface

Voor een moderne chat interface met streaming responses:

```bash
# Start beide servers (aanbevolen)
cd frontend
python start_servers.py

# Of start handmatig:
# Terminal 1: FastAPI backend
python frontend/fastapi_server.py

# Terminal 2: Streamlit frontend  
streamlit run frontend/streamlit_app.py
```

**Open in browser:**
- 🌐 **Chat Interface**: http://localhost:8501
- 📚 **API Documentation**: http://localhost:8000/docs

#### Web Interface Features
- **Real-time streaming** responses
- **Model selection** (GPT-4, Claude, etc.)
- **Custom system prompts** 
- **Chat history** persistence
- **Agent tools inspection**
- **Health monitoring**
- **Mobile responsive** design

### Voorbeelden van Conversaties

De agent kan sophisticate bedrijfstaken uitvoeren:

**📊 Database Analyse:**
- *"Toon alle database tabellen"*
- *"Query de verkoopcijfers van Q4"*
- *"Analyseer onze klantendata en identificeer trends"*

**📧 E-mail Communicatie:**
- *"Stuur een samenvatting naar het management team"*
- *"E-mail de Q4 resultaten naar executives@bedrijf.nl"*
- *"Verstuur een statusupdate naar het projectteam"*

**🔍 Onderzoek & Intelligence:**
- *"Onderzoek de prijsstrategie van onze concurrenten"*
- *"Scrape de nieuwste industrie trends"*
- *"Zoek informatie over marktmogelijkheden in Europa"*

**🧠 Strategische Analyse:**
- *"Help me denken over onze Europese marktexpansie"*
- *"Analyseer de voor- en nadelen van deze productstrategie"*
- *"Welke opties hebben we voor kostenreductie?"*

**⚙️ Workflow Automatisering:**
- *"Voer de quarterly analysis workflow uit"*
- *"Start het competitive research proces"*
- *"Automatiseer het maandrapportage proces"*

## 🔧 Agent Tools

### Database Tools
- `list_tables()` - Toon database schema
- `query_database(sql, max_results)` - Voer SELECT queries uit
- `execute_database(sql, confirm)` - Voer write operaties uit

### Email Tools  
- `send_email(to, subject, body, ...)` - Verstuur e-mails via Microsoft Graph

### Web Research Tools
- `scrape_page(url, extract_links, extract_images)` - Scrape web content
- `search_web(query, max_results)` - Web search met content extractie
- `crawl_website(url, max_pages)` - Website crawling

### Strategic Thinking Tools
- `start_thinking(problem, context)` - Begin gestructureerde analyse
- `add_thought(thought, is_revision)` - Voeg redenering toe
- `finish_thinking()` - Voltooi analyse met oplossing

### Workflow Tools
- `execute_workflow_template(template_name, parameters)` - Voer workflows uit

## 🛡️ Security & Permissions

De agent implementeert uitgebreide security maatregelen:

- **SQL Injection Preventie**: Blokkeert gevaarlijke database queries
- **Email Domain Validatie**: Controleert toegestane e-mail domeinen
- **Permission Checking**: Valideert gebruikersrechten voor alle operaties
- **Confirmation Required**: Vereist bevestiging voor destructieve acties
- **Input Validation**: Complete validatie met Pydantic modellen

## 🧪 Testing

Voer de test suite uit:

```bash
# Basis tests
python -m pytest mcp_business_agent/tests/ -v

# Met coverage
python -m pytest mcp_business_agent/tests/ --cov=mcp_business_agent

# Specifieke test
python -m pytest mcp_business_agent/tests/test_agent.py::TestDatabaseTools -v
```

De test suite bevat:
- **TestModel patronen** voor snelle ontwikkeling
- **Security validatie tests** 
- **Tool functionaliteit tests**
- **Error handling tests**
- **Permission enforcement tests**

## 🔄 Workflow Templates

De agent komt met voorgedefinieerde workflow templates:

### Quarterly Analysis
Uitgebreide kwartaalanalyse workflow:
1. Fetch sales data from database
2. Analyze trends with structured thinking
3. Generate comprehensive report
4. Email results to executives

### Competitive Research  
Multi-step concurrentie onderzoek:
1. Search web for competitor information
2. Scrape competitor pricing pages
3. Analyze findings with strategic thinking
4. Update competitive analysis database

Gebruik met: `"Voer de quarterly_analysis workflow uit"`

## 🚀 Productie Deployment

Voor productie gebruik:

1. **Environment Setup**: Gebruik productie API keys en MCP server URL
2. **Monitoring**: Configureer Pydantic Logfire voor monitoring
3. **Rate Limits**: Pas rate limiting aan voor je use case
4. **Permissions**: Configureer gebruikersrechten per omgeving
5. **Health Checks**: Implementeer health check endpoints

## 📚 Learning Resources & Development

### PydanticAI Examples

Het project bevat uitgebreide learning resources in de `examples/` directory:

#### 🚀 **Basic Chat Agent** (`examples/basic_chat_agent/`)
- Eenvoudige conversational agent implementatie
- Ideaal startpunt voor PydanticAI beginners
- Toont core agent setup patterns

#### 🔧 **Tool-Enabled Agent** (`examples/tool_enabled_agent/`)
- Agent met custom tool implementaties
- Toont `@agent.tool` decorators en parameter validation
- RunContext dependency injection voorbeelden

#### 📊 **Structured Output Agent** (`examples/structured_output_agent/`)
- Agent met Pydantic model outputs
- Result type validation en structured responses
- Perfect voor data extraction use cases

#### 🎯 **Main Agent Reference** (`examples/main_agent_reference/`)
- **Complete reference implementation** voor production agents
- Environment-based configuratie met pydantic-settings
- Multi-provider LLM setup (OpenAI + Anthropic)
- OAuth integration patterns
- Comprehensive error handling
- Testing met TestModel/FunctionModel

#### 🧪 **Testing Examples** (`examples/testing_examples/`)
- TestModel patronen voor snelle ontwikkeling
- FunctionModel voor gecontroleerde test scenarios  
- Agent.override() testing patterns
- Async test patterns met pytest-asyncio

### PRP Methodology (`PRPs/`)

Het project implementeert de **PydanticAI Research Pattern** metodologie:

1. **INITIAL.md** - Definieer agent requirements
2. **Generate PRP** - `/generate-pydantic-ai-prp INITIAL.md`
3. **Execute PRP** - `/execute-pydantic-ai-prp PRPs/filename.md`
4. **Validate** - Test met TestModel/FunctionModel

### Code Structure

De agent volgt PydanticAI best practices:

- **Environment-based configuratie** met pydantic-settings
- **String output by default** (geen result_type tenzij nodig)
- **@agent.tool decorators** met proper RunContext
- **Dependency injection** voor external services
- **Comprehensive error handling** met retry logica

### Extending the Agent

Voeg nieuwe tools toe door:

1. **Tool functie definiëren** met `@business_agent.tool`
2. **Parameters valideren** met Pydantic modellen
3. **MCP client integratie** via `ctx.deps.mcp_client`
4. **Error handling** implementeren
5. **Tests toevoegen** voor nieuwe functionaliteit

## 🆘 Troubleshooting

**Configuratie Issues:**
```bash
# Valideer setup
python -m mcp_business_agent --validate-only

# Check systeem info
python -m mcp_business_agent --status --debug
```

**MCP Connectivity:**
- Controleer MCP_SERVER_URL is correct
- Valideer GITHUB_ACCESS_TOKEN is geldig
- Test MCP server health endpoint

**Permission Errors:**
- Check gebruikersrechten in dependencies
- Valideer email domain configuratie
- Controleer database access permissions

## 🎊 Features & Highlights

### 🤖 Agent Capabilities
✅ **Production-ready** met comprehensive error handling  
✅ **Security-first** met permission checking en input validatie  
✅ **Type-safe** met Pydantic modellen en validation  
✅ **Multi-provider** LLM ondersteuning (OpenAI + Anthropic fallback)  
✅ **15+ MCP Tools** - database, email, web research, strategic thinking  
✅ **OAuth Integration** - GitHub en Microsoft Graph authentication  

### 🌐 Interface Options  
✅ **Dual Interface** - CLI én modern web interface  
✅ **Real-time Streaming** - Live response streaming in web UI  
✅ **Chat History** - Persistent conversation management  
✅ **Health Monitoring** - Real-time system status  
✅ **Mobile Responsive** - Works on desktop en mobile  

### 📚 Learning & Development
✅ **Comprehensive Examples** - 5+ complete PydanticAI implementations  
✅ **PRP Methodology** - Structured agent development workflow  
✅ **Testing Patterns** - TestModel/FunctionModel validation  
✅ **Reference Implementation** - Production-ready agent template  
✅ **Global Development Rules** - CLAUDE.md best practices  

### 🔧 Technical Excellence
✅ **Extensible Architecture** voor custom tools  
✅ **Environment-based Configuration** met pydantic-settings  
✅ **Comprehensive Testing** met pytest en async patterns  
✅ **Rich CLI Formatting** voor professionele output  
✅ **Docker Support** - Container deployment ready  

---

**Ready to automate your business workflows?** 🚀

Start met de CLI interface en ontdek hoe de MCP Business Automation Agent je dagelijkse bedrijfstaken kan transformeren naar intelligente, geautomatiseerde workflows!
