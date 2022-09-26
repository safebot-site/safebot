<h2>To do</h2> 

- validar o certificado de segurança HTPPS;
- validar o orgão emissor do certificado de segurança;
- validar o CNPJ do dono do site com o CNPJ da empresa;
- validar email de contato;
- pesquisar o nível de confiança no Reclame Aqui;
- usar verificacao de antivirus online.


<h2>Doing</h2>
- testing https://badssl.com/ 

<h2>Done</h2>
- verificar se o site suporta conexão segura com HTTPS
- validar SSL

https://us.norton.com/internetsecurity-how-to-how-to-know-if-a-website-is-safe.html 

https://www.rapyd.net/blog/secure-online-payment-processing/

https://www.nerdwallet.com/article/credit-cards/ensure-online-credit-card-purchases-safe


## Como executar

1. Criar ambiente virtual, somente na primeira configuração

<h6> python -m venv venv </h6>  

2. Ativar ambiente virtual
<h6> source venv/bin/activate </h6> 

3. Instalar dependencias

```
pip install -r requirements.txt
```

4. Executar aplicação web

```
uvicorn src.main:app --reload
``

test on: **https://127.0.0.1:8000/verify/google.com
**
