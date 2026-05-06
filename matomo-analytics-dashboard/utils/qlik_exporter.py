import pandas as pd
import os

def export_to_qlik(dataframes_dict, output_dir="exports"):
    """
    Exporta um dicionário de DataFrames para CSVs formatados para o Qlik Sense.
    
    Args:
        dataframes_dict (dict): Ex: {"cities": df_cities, "events": df_events}
        output_dir (str): Nome da pasta de destino.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Diretório '{output_dir}' criado.")

    for name, df in dataframes_dict.items():
        if df is not None and not df.empty:
            filename = os.path.join(output_dir, f"{name}.csv")
            # utf-8-sig garante que o Qlik reconheça acentuação sem configurações extras
            df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';')
            print(f"Exportado: {filename} ({len(df)} linhas)")
        else:
            print(f"Aviso: DataFrame '{name}' está vazio ou é None. Pulando...")

if __name__ == "__main__":
    # Exemplo de uso isolado para teste
    test_df = pd.DataFrame({"Cidade": ["Campo Grande", "Dourados"], "Visitas": [100, 50]})
    export_to_qlik({"teste_qlik": test_df})
