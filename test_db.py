import requests

# Testar a API
try:
    headers = {
        "Accept": "application/json",  # Solicita uma resposta em JSON
        "User-Agent": "VKINHA-Bot/1.0"  # Adiciona um User-Agent para evitar bloqueios
    }
    api_key = '[REDACTED_SECRET]'  # Sua chave de API
    url = f"https://vkinha.com/Bta.php?api_key={api_key}"  # Adiciona a chave na URL

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Dados recebidos da API:")
        print(response.json())  # Exibe os dados JSON
    else:
        print(f"❌ Erro na API: {response.status_code}")
        print("Resposta:", response.text)  # Exibe a resposta bruta para depuração
except Exception as e:
    print(f"❌ Erro ao acessar a API: {e}")