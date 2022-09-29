## Como executar

1. Criar ambiente virtual, somente na primeira configuração

```
python -m venv venv
```

2. Ativar ambiente virtual
```
source venv/bin/activate
```

3. Instalar dependencias

```
pip install -r requirements.txt
```

4. Executar aplicação web

```
uvicorn src.main:app --reload
```
