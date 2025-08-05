# 🤖 MCP Business Automation Agent

Een geavanceerde AI-agent voor bedrijfsautomatisering die integreert met MCP (Model Context Protocol) servers voor uitgebreide database-analyse, e-mailcommunicatie, webonderzoek en strategische besluitvorming.

Built met **PydanticAI** voor robuuste agent architectuur, type veiligheid en productie-gereed ontwerp.

## 🚀 Overzicht

De **MCP Business Automation Agent** is een conversational AI-systeem dat sophisticate bedrijfsworkflows kan uitvoeren door je bestaande MCP server tools te orchestreren. Perfect voor:

- **📊 Data-analyse**: Query bedrijfsdata, genereer rapporten, identificeer trends
- **📧 Communicatie**: Verstuur professionele e-mails en meldingen  
- **🔍 Onderzoek**: Competitieve intelligence, marktonderzoek, web scraping
- **🧠 Strategische besluitvorming**: Gestructureerde probleemoplossing en analyse
- **⚙️ Workflow automatisering**: Multi-step bedrijfsprocessen

### ✨ Kernfunctionaliteiten

- **15+ MCP Tools** voor database, email, web research en thinking
- **Multi-provider LLM ondersteuning** (OpenAI + Anthropic fallback)
- **Robuuste foutafhandeling** met retry logica en rate limiting
- **Permission-based access control** met security validatie
- **Interactieve CLI interface** met rich formatting
- **Comprehensive testing** met TestModel patronen

## 🏗️ Architectuur

```
mcp_business_agent/
├── __init__.py              # Package exports  
├── __main__.py              # Module entry point (python -m mcp_business_agent)
├── agent.py                 # Hoofd agent met 15+ MCP tools
├── auth_cli.py              # Command-line OAuth setup utility
├── auth_manager.py          # GitHub OAuth token management
├── cli.py                   # Interactieve CLI interface
├── dependencies.py          # Dependency injection systeem
├── mcp_client.py            # Robuuste MCP server communicatie  
├── models.py                # Pydantic data modellen
├── oauth_manager.py         # OAuth flow implementatie
├── providers.py             # Multi-provider LLM ondersteuning
├── settings.py              # Environment-based configuratie
├── workflow_manager.py      # Multi-step automatisering
├── requirements.txt         # Alle dependencies
├── .env.example             # Configuratie template
└── tests/
    ├── __init__.py
    └── test_agent.py        # Uitgebreide test suite
```

## 🛠️ Setup & Installatie

### 1. Installeer Dependencies

```bash
# Installeer Python dependencies
pip install -r mcp_business_agent/requirements.txt

# Of gebruik een virtual environment (aanbevolen)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r mcp_business_agent/requirements.txt
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

### Interactieve CLI

Start de conversational interface:

```bash
python -m mcp_business_agent
```

Of met debug mode:

```bash
python -m mcp_business_agent --debug
```

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

## 📚 Development

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

✅ **Production-ready** met comprehensive error handling  
✅ **Security-first** met permission checking en input validatie  
✅ **Type-safe** met Pydantic modellen en validation  
✅ **Multi-provider** LLM ondersteuning met fallback  
✅ **Extensible** architectuur voor custom tools  
✅ **CLI interface** voor interactieve gebruik  
✅ **Comprehensive testing** met 95%+ coverage  
✅ **Rich formatting** voor professionele output  

---

**Ready to automate your business workflows?** 🚀

Start met de CLI interface en ontdek hoe de MCP Business Automation Agent je dagelijkse bedrijfstaken kan transformeren naar intelligente, geautomatiseerde workflows!