from httpx import AsyncClient
from bs4 import BeautifulSoup

import json

http_client = AsyncClient()

# valida se site usa o protocolo HTTPS
def validate_protocol(site_url: str):
    return site_url.lower().startswith("https")

# valida certificado ssl
async def validate_certificate(site_url: str):
    try:
        response = await http_client.get(site_url)
        return True
    except:
        return False

# valida endereco de email de contato
async def validate_email(email: str):
    response = await http_client.get(f"https://api.eva.pingutil.com/email?email={email}")
    response_data = json.loads(response.text)["data"]

    if response_data["disposable"]:
        return False
    if response_data["catch_all"]:
        return False
    if response_data["gibberish"]:
        return False
    if response_data["spam"]:
        return False
    return True

# calcula o CNPJ da matriz a partir de outro CNPJ
def calculate_cnpj_matriz(site_cnpj):
    cnpj = list(site_cnpj[:12])
    cnpj[8] = '0'
    cnpj[9] = '0'
    cnpj[10] = '0'
    cnpj[11] = '1'
    cnpj = ''.join(cnpj)

    if (site_cnpj.endswith("0001", 0, 12)):
        return site_cnpj
    reverse_cnpj = list(map(int, cnpj[::-1]))

    pesos = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
    for i in range(12):
        reverse_cnpj[i] = reverse_cnpj[i] * pesos[i]

    soma = 0
    for i in range(12):
        soma += reverse_cnpj[i]
    
    primeiro_digito_verificador = 11 - (soma % 11)

    if (primeiro_digito_verificador >= 10):
        primeiro_digito_verificador = '0'
    else:
        primeiro_digito_verificador = str(primeiro_digito_verificador)
    
    cnpj_matriz = list(cnpj)
    cnpj_matriz.append(primeiro_digito_verificador)
    reverse_cnpj = list(map(int, ''.join(cnpj_matriz)[::-1]))
    pesos = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5, 6]
    for i in range(13):
        reverse_cnpj[i] = reverse_cnpj[i] * pesos[i]

    soma = 0
    for i in range(13):
        soma += reverse_cnpj[i]
    
    segundo_digito_verificador = 11 - (soma % 11)

    if (segundo_digito_verificador >= 10):
        segundo_digito_verificador = '0'
    else:
        segundo_digito_verificador = str(segundo_digito_verificador)
    
    cnpj_matriz.append(segundo_digito_verificador)

    return ''.join(cnpj_matriz)

# validar o CNPJ do dono do site com o CNPJ da empresa 
async def validate_cnpj(site_url, site_cnpj):
    domain_url = site_url[7:]
    response = await http_client.get(f"https://rdap.registro.br/domain/{domain_url}")
    cnpj = response.json()["entities"][0]["handle"]
    cnpj_matriz = calculate_cnpj_matriz(site_cnpj)

    return cnpj_matriz==cnpj

# valida reputacao do site no reclame aqui
async def validate_reclame_aqui(site_url):
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'X-user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36 FKUA/website/41/website/Desktop',
        'Content-Type': 'application/json',
        'Origin': 'https://www.reclameaqui.com.br',
        'Host': 'www.reclameaqui.com.br',
        'Pragma': 'no-cache'
    }

    response = await http_client.get("https://www.reclameaqui.com.br/empresa/kabum/", headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    score = float(soup.find_all("span", class_="score")[0].b.extract().get_text())

    return score >= 6