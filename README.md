<h2>To do</h2> 

- validar o certificado de segurança HTPPS
- validar o orgão emissor do certificado de segurança
- validar o CNPJ do dono do site com o CNPJ da empresa
- validar email de contato
- pesquisar o nível de confiança no Reclame Aqui
- usar verificacao de antivirus online


<h2>Doing</h2>
- 

Done
- verificar se o site suporta conexão segura com HTTPS
- validar SSL

https://us.norton.com/internetsecurity-how-to-how-to-know-if-a-website-is-safe.html 

## Como executar

1. Criar ambiente virtual, somente na primeira configuração
python -m venv venv 

2. Ativar ambiente virtual
source venv/bin/activate

3. Instalar dependencias

```
pip install -r requirements.txt
```

4. Executar aplicação web

```
uvicorn main:app --reload
``
