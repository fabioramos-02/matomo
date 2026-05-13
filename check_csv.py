import csv

path = "matomo-analytics-dashboard/exports/cartas_errors.csv"
with open(path, 'r', encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f, delimiter=';')
    header = next(reader)
    num_cols = len(header)
    print(f"Header has {num_cols} columns: {header}")
    
    for i, row in enumerate(reader, start=2):
        if len(row) != num_cols:
            print(f"Error at line {i}: expected {num_cols} columns, got {len(row)}")
            print(f"Row content: {row}")
            break
    else:
        print("CSV structure is consistent.")
