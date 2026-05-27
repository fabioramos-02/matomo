import plotly.express as px

def create_top_bar_chart(df, x_col, y_col, color_scale, color_col=None, margin_r=110):
    """
    Cria um gráfico de barras horizontais com a primeira barra destacada (negrito, texto dentro)
    e as demais com texto por fora.
    """
    n_items = len(df)
    labels, textpositions, textcolors, textsizes = [], [], [], []
    
    _color = color_col if color_col else x_col
    
    # Heurística para a cor do texto da primeira barra
    first_text_color = '#FFFFFF'
    if color_col and n_items > 0:
        val = df.iloc[0][color_col]
        if isinstance(val, (int, float)) and val < 40:
            first_text_color = '#111827' # Dark text for light bars

    if n_items > 0:
        for i, v in enumerate(df[x_col]):
            formatted = f"{v:,}".replace(",", ".")
            if i == 0:
                labels.append(f"<b>{formatted}</b>")
            else:
                labels.append(formatted)
        textpositions = ['inside'] + ['outside'] * (n_items - 1)
        textcolors = [first_text_color] + ['#E0E0E0'] * (n_items - 1)
        textsizes = [13] + [11] * (n_items - 1)
        
    fig = px.bar(df, x=x_col, y=y_col, orientation='h', color=_color, color_continuous_scale=color_scale, text=labels)
    fig.update_traces(
        texttemplate='%{text}',
        textposition=textpositions,
        textfont=dict(color=textcolors, size=textsizes),
        insidetextanchor='end'
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(r=margin_r, t=20, b=20, l=20))
    return fig

def format_pie_chart(fig):
    """
    Formata um gráfico de pizza para ter as legendas dentro (label e porcentagem),
    removendo a legenda externa.
    """
    fig.update_traces(
        textposition="inside",
        texttemplate="<b>%{label}<br>%{percent:.1%}</b>",
        insidetextfont=dict(size=16)
    )
    fig.update_layout(showlegend=False, margin=dict(t=20, b=20))
    return fig
