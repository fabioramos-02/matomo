import pandas as pd
import re

def process_page_urls(data):
    """Transforma a resposta JSON de getPageUrls em um DataFrame plano."""
    rows = []
    
    def extract_nodes(nodes, prefix=""):
        for node in nodes:
            label = node.get('label', '')
            # O label retornado pela API muitas vezes é o path da URL
            url_path = f"{prefix}{label}"
            
            rows.append({
                'URL': url_path,
                'Visitas': node.get('nb_visits', 0),
                'Tempo_Medio': node.get('avg_time_on_page', 0),
                'Taxa_Rejeicao': node.get('bounce_rate', '0%')
            })
            
            # Se houver subpáginas, extrai recursivamente
            if 'subtable' in node and isinstance(node['subtable'], list):
                # Alguns labels vem com '/' no começo, então ajustamos o prefixo
                new_prefix = url_path if url_path.endswith('/') else f"{url_path}/"
                extract_nodes(node['subtable'], new_prefix)

    if isinstance(data, list):
        extract_nodes(data)
        
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by='Visitas', ascending=False).reset_index(drop=True)
    return df

def identify_service_cards(df):
    """
    Filtra o DataFrame para encontrar possíveis "Cartas de Serviço".
    Como não há um padrão exato, usamos heurísticas:
    1. A URL contém hifens (ex: solicitar-algo, agendar-atendimento).
    2. Não é uma página raiz genérica como /index ou /busca.
    3. Possui verbos ou substantivos de ação comuns.
    """
    if df.empty:
        return df
        
    # Palavras-chave que indicam um serviço
    keywords = ['requerer', 'solicitar', 'agendar', 'pagar', 'consultar', 'emitir', 'atendimento', 'declaracao', 'certidao']
    
    def is_service(url):
        url_lower = url.lower()
        # Ignora páginas genéricas
        if url_lower in ['/', '/index', '/busca', '/search']:
            return False
            
        # Padrão: URL tem hífen e não tem extensão de arquivo comum
        has_hyphen = '-' in url_lower
        no_file_ext = not re.search(r'\.(jpg|png|pdf|css|js)$', url_lower)
        
        # Opcional: checa se tem alguma keyword
        has_keyword = any(kw in url_lower for kw in keywords)
        
        # A combinação de hifen + sem extensão já filtra bastante as notícias vs páginas raiz.
        # Adicionar a exigência de keyword torna mais estrito.
        return has_hyphen and no_file_ext and has_keyword

    service_df = df[df['URL'].apply(is_service)].copy()
    return service_df.head(20) # Top 20 serviços

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

def process_transitions(data):
    """Processa os dados de transição de uma página para entender a jornada."""
    if not data or not isinstance(data, dict):
        return {}
        
    previous = data.get('previousPages', [])
    following = data.get('followingPages', [])
    
    # Pega top 5 origens e destinos
    top_prev = sorted(previous, key=lambda x: x.get('referrals', 0), reverse=True)[:5]
    top_next = sorted(following, key=lambda x: x.get('hits', 0), reverse=True)[:5]
    
    return {
        'origens': [{'URL': p.get('label'), 'Visitas': p.get('referrals')} for p in top_prev],
        'destinos': [{'URL': p.get('label'), 'Visitas': p.get('hits')} for p in top_next]
    }

def process_cities_ms(data):
    """Processa a lista de cidades e filtra apenas as do Mato Grosso do Sul."""
    if not data or not isinstance(data, list):
        return pd.DataFrame()
    
    rows = []
    for item in data:
        label = item.get('label', '')
        # Se for do MS, o label normalmente vem como "Cidade, Mato Grosso do Sul, Brazil"
        if "Mato Grosso do Sul" in label:
            # Pega só o nome da cidade, antes da vírgula
            city_name = label.split(",")[0].strip()
            rows.append({
                'Cidade': city_name,
                'Visitas': item.get('nb_visits', 0)
            })
    
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by='Visitas', ascending=False).reset_index(drop=True)
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
    """Processa a lista de navegadores."""
    if not data or not isinstance(data, list):
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    if 'label' in df.columns and 'nb_visits' in df.columns:
        df = df[['label', 'nb_visits']].rename(columns={'label': 'Navegador', 'nb_visits': 'Visitas'})
        return df.head(10)
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
