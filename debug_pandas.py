
import pandas as pd
import os

with open('debug.csv', 'w', encoding='utf-8') as f:
    f.write("Just a keyword\nAnother keyword")

try:
    df = pd.read_csv('debug.csv', sep=None, engine='python', encoding='utf-8')
    print("DataFrame:")
    print(df)
    print("\nColumns:")
    print(df.columns.tolist())
    
    col = df.columns[0]
    print(f"\nFirst Column: {col}")
    
    vals = df[col].dropna().astype(str).tolist()
    print(f"\nValues in First Column: {vals}")
    
    combined = [str(col)] + vals
    print(f"\nCombined: {combined}")
    
except Exception as e:
    print(f"Error: {e}")

try:
    os.remove('debug.csv')
except:
    pass
