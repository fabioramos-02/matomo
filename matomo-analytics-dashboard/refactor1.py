import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove cache
content = content.replace('@st.cache_resource\ndef get_api():', 'def get_api():')

# 2. Reorganize tabs
content = re.sub(
    r'tab1, tab2, tab3, tab4 = st.tabs\(\[.*?\]\)',
    'tab1, tab2, tab3, tab4 = st.tabs([\n    "1. Perfil do Cidadão",\n    "2. Intenção de Busca",\n    "3. Serviços Consumidos",\n    "4. Fluxo de Navegação"\n])',
    content,
    flags=re.DOTALL
)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
