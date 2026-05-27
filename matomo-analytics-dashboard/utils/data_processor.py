import pandas as pd
import re
from urllib.parse import unquote

def process_page_urls(data):
    """Transforma a resposta JSON de getPageUrls em um DataFrame plano."""
    if not data:
        print("⚠️ process_page_urls: Dados vazios.")
        return pd.DataFrame()
    
    rows = []
    
    def extract_nodes(nodes, prefix=""):
        for node in nodes:
            label = node.get('label', '')
            url_path = f"{prefix}{label}"
            rows.append({
                'URL': url_path,
                'Visitas': node.get('nb_visits', 0),
                'Tempo_Medio': node.get('avg_time_on_page', 0),
                'Taxa_Rejeicao': node.get('bounce_rate', '0%')
            })
            if 'subtable' in node and isinstance(node['subtable'], list):
                new_prefix = url_path if url_path.endswith('/') else f"{url_path}/"
                extract_nodes(node['subtable'], new_prefix)

    if isinstance(data, list):
        extract_nodes(data)
        
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by='Visitas', ascending=False).reset_index(drop=True)
    print(f"📊 process_page_urls: {len(df)} URLs processadas.")
    return df

# Mapeamento oficial de categorias do Portal de Serviços
CATEGORIAS_MAPEAMENTO = {
    "administracao-publica": "Administração Pública",
    "agropecuaria-e-vida-rural": "Agropecuária e Vida Rural",
    "arte-e-cultura": "Arte e Cultura",
    "assistencia-social": "Assistência Social",
    "ciencia-e-tecnologia": "Ciência e Tecnologia",
    "comunicacao-e-transparencia": "Comunicação e Transparência",
    "direitos-e-cidadania": "Direitos e Cidadania",
    "educacao-e-pesquisa": "Educação e Pesquisa",
    "empresa-industria-e-comercio": "Empresa, Indústria e Comércio",
    "energia": "Energia",
    "esporte-e-lazer": "Esporte e Lazer",
    "financas-e-impostos": "Finanças e Impostos",
    "forcas-armadas-e-defesa-civil": "Forças Armadas e Defesa Civil",
    "habitacao": "Habitação",
    "infraestrutura": "Infraestrutura",
    "justica": "Justiça",
    "meio-ambiente": "Meio Ambiente",
    "saude-e-cuidado": "Saúde e Cuidado",
    "seguranca": "Segurança",
    "trabalho-emprego-e-previdencia": "Trabalho, Emprego e Previdência",
    "transito-e-transportes": "Trânsito e Transportes",
    "turismo": "Turismo"
}

def identify_service_cards(df):
    """
    Filtra o DataFrame do Matomo para encontrar 'Cartas de Serviço'.
    Cruza com o inventário oficial para garantir que os slugs, títulos, órgãos e modalidades estão corretos.
    Retorna SOMENTE os serviços ATIVOS listados no inventário.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    from utils.cartas_data_loaders import load_service_cards_inventory

    try:
        # Carrega os dados mais recentes do banco ou CSV via loader
        df_inv = load_service_cards_inventory()
        # Filtra apenas serviços ativos
        df_inv = df_inv[df_inv['servico_ativo'] == True]
        
        inventory_map = {}
        if not df_inv.empty:
            for _, inv_row in df_inv.iterrows():
                key = (str(inv_row['slug_categoria']).lower(), str(inv_row['slug_servico']).lower())
                
                # Determinar Modalidade
                modalidade = "Presencial"
                if inv_row.get('digital') == True:
                    modalidade = "Digital"
                elif inv_row.get('online') == True:
                    modalidade = "Híbrido"
                    
                inventory_map[key] = {
                    'titulo': inv_row['titulo_servico'],
                    'categoria_nome': inv_row.get('nome_categoria') if pd.notna(inv_row.get('nome_categoria')) else str(inv_row['slug_categoria']).replace('-', ' ').title(),
                    'sigla_orgao': inv_row.get('siglaorgao', 'Não Identificado'),
                    'nome_orgao': inv_row.get('nome_orgao', 'Não Identificado'),
                    'modalidade': modalidade
                }
        print(f"✅ Inventário de serviços ATIVOS carregado para cruzamento: {len(inventory_map)} itens.")
    except Exception as e:
        print(f"⚠️ Erro ao carregar inventário para cruzamento: {e}")
        inventory_map = {}

    rows = []
    for _, row in df.iterrows():
        url = str(row['URL'])
        parts = [p for p in url.split('/') if p]
        if len(parts) >= 2:
            categoria_raw = parts[0].lower()
            slug_raw = parts[1]
            
            # Match Exato com Inventário (Apenas Ativos)
            key = (categoria_raw, slug_raw.lower())
            if key in inventory_map:
                inv_data = inventory_map[key]
                rows.append({
                    'URL_Original': url,
                    'slug_servico': slug_raw,
                    'slug_categoria': categoria_raw,
                    'Categoria': inv_data['categoria_nome'],
                    'Nome do Serviço': inv_data['titulo'],
                    'Órgão': inv_data['sigla_orgao'],
                    'Nome do Órgão': inv_data['nome_orgao'],
                    'Modalidade': inv_data['modalidade'],
                    'Visitas': row['Visitas'],
                    'Link': f"https://www.ms.gov.br/{categoria_raw}/{slug_raw}"
                })

    service_df = pd.DataFrame(rows)
    if not service_df.empty:
        # Agrupa para somar visitas de URLs que podem ter variações de parâmetros mas mesmo slug
        cols_groupby = ['slug_servico', 'slug_categoria', 'Categoria', 'Nome do Serviço', 'Órgão', 'Nome do Órgão', 'Modalidade', 'Link']
        service_df = service_df.groupby(cols_groupby, as_index=False).agg({'Visitas': 'sum', 'URL_Original': 'first'})
        service_df = service_df.sort_values(by='Visitas', ascending=False).reset_index(drop=True)
        
    print(f"🃏 identify_service_cards: {len(service_df)} cartas de serviço ATIVAS cruzadas.")
    return service_df

def process_search_keywords(data):
    """Transforma a resposta de SiteSearch em um DataFrame."""
    if not data or not isinstance(data, list):
        return pd.DataFrame()

    df = pd.DataFrame(data)
    if 'label' in df.columns and 'nb_visits' in df.columns:
        df = df[['label', 'nb_visits']].rename(columns={'label': 'Palavra-chave', 'nb_visits': 'Buscas'})
        # Filtra sujeira (as vezes URLs aparecem nas buscas)
        df = df[~df['Palavra-chave'].str.startswith('/')]
        return df.head(20)
    return pd.DataFrame()

def extract_search_from_page_urls(df_pages):
    """Extrai termos de busca de URLs /buscar/q=* ou /q=* do portal ms.gov.br."""
    if df_pages is None or df_pages.empty:
        return pd.DataFrame()

    mask = df_pages['URL'].str.contains(r'(?:buscar/)?q=', regex=True, na=False)
    df_q = df_pages[mask].copy()

    def extrair_termo(url):
        m = re.search(r'[?/]q=([^&/]+)', url)
        if m:
            return unquote(m.group(1)).strip().lower()
        return None

    df_q['Palavra-chave'] = df_q['URL'].apply(extrair_termo)
    df_q = df_q.dropna(subset=['Palavra-chave'])
    df_q = df_q[df_q['Palavra-chave'] != '']

    if df_q.empty:
        return pd.DataFrame()

    result = df_q.groupby('Palavra-chave', as_index=False)['Visitas'].sum()
    result = result.rename(columns={'Visitas': 'Buscas'})
    result = result.sort_values('Buscas', ascending=False).reset_index(drop=True)
    print(f"🔍 extract_search_from_page_urls: {len(result)} termos de busca extraídos de URLs.")
    return result

def process_transitions(data):
    """Processa os dados de transição de uma página para entender a jornada."""
    if not data or not isinstance(data, dict):
        return {}
        
    previous = data.get('previousPages', [])
    following = data.get('followingPages', [])
    
    # Ordena por visitas
    top_prev = sorted(previous, key=lambda x: x.get('referrals', 0), reverse=True)
    top_next = sorted(following, key=lambda x: x.get('hits', 0), reverse=True)
    
    return {
        'origens': [{'URL': p.get('label'), 'Visitas': p.get('referrals')} for p in top_prev],
        'destinos': [{'URL': p.get('label'), 'Visitas': p.get('hits')} for p in top_next],
        'followingPages': following # Mantém os dados originais para o macro-fluxo
    }

def process_cities_ms(data):
    """Processa a lista de cidades e filtra apenas as do Mato Grosso do Sul."""
    if not data or not isinstance(data, list):
        print("⚠️ process_cities_ms: Dados vazios ou inválidos.")
        return pd.DataFrame()
    
    rows = []
    for item in data:
        label = item.get('label', '')
        if "Mato Grosso do Sul" in label:
            city_name = label.split(",")[0].strip()
            city_name = re.sub(r'\s*\(.*?\)', '', city_name).strip()
            rows.append({
                'Cidade': city_name,
                'Visitas': item.get('nb_visits', 0)
            })
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.groupby('Cidade', as_index=False)['Visitas'].sum()
        df = df.sort_values(by='Visitas', ascending=False).reset_index(drop=True)
    print(f"📍 process_cities_ms: {len(df)} cidades do MS processadas.")
    return df

def process_visit_time(data):
    """Processa dados de horário do servidor para gráfico de linha."""
    if not data or not isinstance(data, list):
        return pd.DataFrame()
        
    df = pd.DataFrame(data)
    if 'label' in df.columns and 'nb_visits' in df.columns:
        df = df[['label', 'nb_visits']].rename(columns={'label': 'Hora', 'nb_visits': 'Visitas'})
        # A hora vem como string (ex: '0h', '14h'), vamos ordenar se possível
        # ou apenas deixar como vem.
        return df
    return pd.DataFrame()

def process_browsers(data):
    """Processa a lista de navegadores e agrupa o restante em 'Outros'."""
    if not data or not isinstance(data, list):
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    if 'label' in df.columns and 'nb_visits' in df.columns:
        df = df[['label', 'nb_visits']].rename(columns={'label': 'Navegador', 'nb_visits': 'Visitas'})
        
        if len(df) > 5:
            df = df.sort_values(by='Visitas', ascending=False).reset_index(drop=True)
            top_4 = df.head(4)
            outros_visitas = df.iloc[4:]['Visitas'].sum()
            df_outros = pd.DataFrame([{'Navegador': 'Outros', 'Visitas': outros_visitas}])
            df = pd.concat([top_4, df_outros], ignore_index=True)
            
        return df
    return pd.DataFrame()

def process_device_types(data):
    """Processa tipos de dispositivo."""
    if not data or not isinstance(data, list):
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    if 'label' in df.columns and 'nb_visits' in df.columns:
        df = df[['label', 'nb_visits']].rename(columns={'label': 'Dispositivo', 'nb_visits': 'Visitas'})
        
        if len(df) > 3:
            df = df.sort_values(by='Visitas', ascending=False).reset_index(drop=True)
            top_2 = df.head(2)
            outros_visitas = df.iloc[2:]['Visitas'].sum()
            df_outros = pd.DataFrame([{'Dispositivo': 'Outros', 'Visitas': outros_visitas}])
            df = pd.concat([top_2, df_outros], ignore_index=True)
            
        return df
    return pd.DataFrame()

_EXT_RE = re.compile(r'\.(jpg|png|pdf|css|js)$', re.IGNORECASE)
_VALID_CATS = set(CATEGORIAS_MAPEAMENTO.keys())
_DIGIT_TRAIL_RE = re.compile(r'\d+$')


def process_services_trend(daily_data, top_services):
    """
    daily_data: dict {date_str: list_of_url_nodes} — resposta de get_page_urls_trend
    top_services: lista de nomes de serviços (str) para filtrar
    Retorna DataFrame com colunas: Data, Serviço, Visitas

    Otimizado: loop direto nos nós brutos sem reconstruir DataFrame por dia.
    """
    if not daily_data or not isinstance(daily_data, dict) or not top_services:
        return pd.DataFrame()

    top_set = set(top_services)
    rows = []

    for date_str, url_data in sorted(daily_data.items()):
        if not url_data or not isinstance(url_data, list):
            continue
        try:
            data_parsed = pd.to_datetime(date_str)
        except Exception:
            continue

        daily_visits: dict[str, int] = {}
        for node in url_data:
            url = node.get('label', '')
            visits = node.get('nb_visits', 0) or 0
            parts = [p for p in url.split('/') if p]
            if len(parts) < 2:
                continue
            cat_raw = parts[0].lower()
            if cat_raw not in _VALID_CATS:
                continue
            slug = parts[1]
            if '-' not in slug or _EXT_RE.search(slug):
                continue
            svc_name = _DIGIT_TRAIL_RE.sub('', slug).replace('-', ' ').title()
            if svc_name not in top_set:
                continue
            daily_visits[svc_name] = daily_visits.get(svc_name, 0) + visits

        for svc, vis in daily_visits.items():
            rows.append({'Data': data_parsed, 'Serviço': svc, 'Visitas': vis})

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values(['Data', 'Serviço'])
        .reset_index(drop=True)
    )


def process_matomo_summary(data):
    """Processa o resumo de visitas do Matomo."""
    if not data or not isinstance(data, dict):
        return pd.DataFrame()
    
    # Transforma o dicionário em uma linha de DataFrame
    df = pd.DataFrame([data])
    
    # Renomeia colunas para ficar mais amigável no Qlik
    mapping = {
        'nb_visits': 'Visitas',
        'nb_actions': 'Ações',
        'nb_users': 'Usuários Únicos',
        'max_actions': 'Máximo de Ações',
        'sum_visit_length': 'Tempo Total (s)',
        'bounce_count': 'Rejeições',
        'nb_visits_converted': 'Conversões'
    }
    
    df = df.rename(columns=mapping)
    # Mantém apenas as colunas mapeadas que existirem no dado
    cols_to_keep = [c for c in mapping.values() if c in df.columns]
    return df[cols_to_keep]

