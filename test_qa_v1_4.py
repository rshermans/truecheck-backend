"""
TrueCheck v1.3.0/v1.4.0 - QA Test Suite
Tests for Multi-Source News Aggregation and Admin Dashboard
"""
import asyncio
import httpx
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api"
ADMIN_TOKEN = None  # Will be set after login

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, status, details=""):
    symbol = "✓" if status else "✗"
    color = Colors.GREEN if status else Colors.RED
    print(f"{color}{symbol} {name}{Colors.END}")
    if details:
        print(f"  {Colors.YELLOW}{details}{Colors.END}")

async def login_admin():
    """Login as admin to get token"""
    global ADMIN_TOKEN
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json={
                "username": "rshermans",
                "password": "TRUEcheck@2025"
            })
            if response.status_code == 200:
                data = response.json()
                # API returns {access_token: "...", token_type: "bearer"}
                ADMIN_TOKEN = data.get("access_token") or data.get("token")
                if ADMIN_TOKEN:
                    print_test("Admin Login", True, f"Token: {ADMIN_TOKEN[:20]}...")
                    return True
                else:
                    print_test("Admin Login", False, f"No token in response: {data}")
                    return False
            else:
                print_test("Admin Login", False, f"Status: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_test("Admin Login", False, str(e))
            return False

async def test_get_sources():
    """Test GET /api/news/sources"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/news/sources",
                headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
            )
            if response.status_code == 200:
                sources = response.json()
                print_test("GET /news/sources", True, f"Found {len(sources)} sources")
                for src in sources:
                    status_icon = "🟢" if src['enabled'] else "🔴"
                    print(f"    {status_icon} {src['name']} ({src['type']})")
                return sources
            else:
                print_test("GET /news/sources", False, f"Status: {response.status_code}")
                return []
        except Exception as e:
            print_test("GET /news/sources", False, str(e))
            return []

async def test_toggle_source(source_id, enable):
    """Test POST /api/news/sources/toggle"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/news/sources/toggle",
                params={"source_id": source_id, "enabled": enable},
                headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
            )
            action = "Ativar" if enable else "Desativar"
            if response.status_code == 200:
                print_test(f"Toggle {source_id} ({action})", True)
                return True
            else:
                print_test(f"Toggle {source_id}", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            print_test(f"Toggle {source_id}", False, str(e))
            return False

async def test_update_news_feed():
    """Test POST /api/news/update (Aggregation)"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print(f"{Colors.BLUE}⏳ Sincronizando fontes (pode demorar)...{Colors.END}")
            response = await client.post(
                f"{BASE_URL}/news/update",
                headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
            )
            if response.status_code == 200:
                data = response.json()
                print_test("News Aggregation", True, data.get("message"))
                return True
            else:
                print_test("News Aggregation", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            print_test("News Aggregation", False, str(e))
            return False

async def test_get_news_with_filters():
    """Test GET /api/news with various filters"""
    async with httpx.AsyncClient() as client:
        # Test 1: No filters
        try:
            response = await client.get(f"{BASE_URL}/news/")
            if response.status_code == 200:
                all_news = response.json()
                print_test("GET /news (sem filtros)", True, f"{len(all_news)} artigos")
            else:
                print_test("GET /news (sem filtros)", False)
        except Exception as e:
            print_test("GET /news (sem filtros)", False, str(e))
        
        # Test 2: Filter by verdict
        try:
            response = await client.get(f"{BASE_URL}/news/?verdict=Falso")
            if response.status_code == 200:
                falso_news = response.json()
                print_test("Filtro: verdict=Falso", True, f"{len(falso_news)} artigos")
            else:
                print_test("Filtro: verdict=Falso", False)
        except Exception as e:
            print_test("Filtro: verdict=Falso", False, str(e))
        
        # Test 3: Filter by date range
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            response = await client.get(
                f"{BASE_URL}/news/?start_date={start_date}&end_date={end_date}"
            )
            if response.status_code == 200:
                dated_news = response.json()
                print_test(f"Filtro: Últimos 30 dias", True, f"{len(dated_news)} artigos")
            else:
                print_test("Filtro: Data", False)
        except Exception as e:
            print_test("Filtro: Data", False, str(e))
        
        # Test 4: Combined filters
        try:
            response = await client.get(
                f"{BASE_URL}/news/?verdict=Verdadeiro&language=pt"
            )
            if response.status_code == 200:
                combined = response.json()
                print_test("Filtro: Combinado (Verdadeiro + PT)", True, f"{len(combined)} artigos")
            else:
                print_test("Filtro: Combinado", False)
        except Exception as e:
            print_test("Filtro: Combinado", False, str(e))

async def test_sources_config_persistence():
    """Test if source config persists to JSON file"""
    import os
    config_file = "sources_config.json"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print_test("Config Persistence (JSON)", True, f"{len(config)} fontes salvas")
            print(f"    {Colors.BLUE}Conteúdo: {json.dumps(config, indent=2)}{Colors.END}")
        except Exception as e:
            print_test("Config Persistence", False, str(e))
    else:
        print_test("Config Persistence", False, "Arquivo sources_config.json não encontrado")

async def run_all_tests():
    """Run complete test suite"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("🧪 TrueCheck QA Test Suite - v1.3.0/v1.4.0")
    print(f"{'='*60}{Colors.END}\n")
    
    # Phase 1: Authentication
    print(f"{Colors.BLUE}📌 FASE 1: Autenticação{Colors.END}")
    if not await login_admin():
        print(f"{Colors.RED}❌ Testes abortados: Falha no login{Colors.END}")
        return
    print()
    
    # Phase 2: Source Management
    print(f"{Colors.BLUE}📌 FASE 2: Gestão de Fontes{Colors.END}")
    sources = await test_get_sources()
    print()
    
    if sources:
        # Test toggling first source
        first_source = sources[0]
        print(f"{Colors.BLUE}📌 FASE 3: Toggle de Fontes{Colors.END}")
        await test_toggle_source(first_source['id'], not first_source['enabled'])
        await asyncio.sleep(1)
        await test_toggle_source(first_source['id'], first_source['enabled'])  # Restore
        print()
    
    # Phase 4: Config Persistence
    print(f"{Colors.BLUE}📌 FASE 4: Persistência de Configuração{Colors.END}")
    await test_sources_config_persistence()
    print()
    
    # Phase 5: News Aggregation
    print(f"{Colors.BLUE}📌 FASE 5: Agregação de Notícias{Colors.END}")
    await test_update_news_feed()
    print()
    
    # Phase 6: News Filters
    print(f"{Colors.BLUE}📌 FASE 6: Filtros de Notícias{Colors.END}")
    await test_get_news_with_filters()
    print()
    
    print(f"{Colors.GREEN}{'='*60}")
    print("✅ Testes Concluídos!")
    print(f"{'='*60}{Colors.END}\n")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
