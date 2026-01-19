import httpx
import asyncio
from config import settings

async def test_google_api():
    if not settings.GOOGLE_FACT_CHECK_API_KEY:
        print("❌ GOOGLE_FACT_CHECK_API_KEY not configured")
        return
    
    print(f"✅ API Key configured (length: {len(settings.GOOGLE_FACT_CHECK_API_KEY)})")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                params={
                    "key": settings.GOOGLE_FACT_CHECK_API_KEY,
                    "query": "fact check",
                    "languageCode": "pt",
                    "pageSize": 1
                },
                timeout=10.0
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                claims = data.get("claims", [])
                print(f"✅ API working! Found {len(claims)} claim(s)")
                if claims:
                    print(f"Sample: {claims[0].get('text', 'N/A')[:100]}")
            else:
                print(f"❌ API Error: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_google_api())
