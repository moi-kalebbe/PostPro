
import os
import pandas as pd
import logging

# Mock objects
class MockFile:
    def __init__(self, path):
        self.path = path

class MockBatchJob:
    def __init__(self, path):
        self.csv_file = MockFile(path)

# Mock logger
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARN: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")

logger = MockLogger()

# Definition of the function to test (copied from tasks.py to avoid importing django)
def read_keywords_from_file(batch_job) -> list[str]:
    """
    Read keywords from CSV or XLSX file with robust encoding and delimiter detection.
    """
    import csv
    
    if not batch_job.csv_file:
        return []
    
    file_path = batch_job.csv_file.path
    
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'utf-8-sig']
        df = None
        error_msg = ""
        
        for encoding in encodings:
            try:
                # Use sniffing to find delimiter
                sep = ',' # Default
                try:
                    with open(file_path, 'r', encoding=encoding, newline='') as csvfile:
                        # Read a sample. If file is small, read all.
                        sample = csvfile.read(2048)
                        if not sample: # Empty file
                            continue
                        sniffer = csv.Sniffer()
                        dialect = sniffer.sniff(sample, delimiters=[',', ';', '\t', '|'])
                        sep = dialect.delimiter
                except Exception:
                    # Fallback to comma if sniffing fails (e.g. single column)
                    sep = ','
                
                df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                logger.info(f"Successfully read CSV with encoding {encoding} and separator '{sep}'")
                break
            except Exception as e:
                error_msg = str(e)
                continue
        
        if df is None:
            raise ValueError(f"Could not read CSV file. Last error: {error_msg}")
    
    # Look for keyword column
    keyword_col = None
    target_cols = ['keyword', 'keywords', 'palavra-chave', 'palavra_chave', 'topic', 'tema', 'assunto']
    
    for col in df.columns:
        if str(col).lower().strip() in target_cols:
            keyword_col = col
            break
    
    if keyword_col is None:
        # Use first column if it looks like text
        keyword_col = df.columns[0]
        logger.warning(f"No keyword column found. Using first column: {keyword_col}")
        
        # If we fell back to the first column (likely because of missing header), 
        # include the header itself as it might be a keyword.
        keywords = [str(keyword_col)] + df[keyword_col].dropna().astype(str).tolist()
    else:
        keywords = df[keyword_col].dropna().astype(str).tolist()
    
    # Clean and filter
    keywords = [k.strip() for k in keywords if k.strip()]
    
    if not keywords:
        raise ValueError("No valid keywords found in file")
        
    return keywords

# Test Runner
def run_tests():
    print("--- Starting CSV Robustness Tests ---")
    
    # 1. Test UTF-8 with comma
    print("\nTest 1: UTF-8 Comma")
    with open('test_utf8.csv', 'w', encoding='utf-8') as f:
        f.write("keywords\nkeyword1\nkeyword2")
    
    try:
        k = read_keywords_from_file(MockBatchJob('test_utf8.csv'))
        print(f"Result: {k}")
        assert "keyword1" in k
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")

    # 2. Test Latin-1 with Semicolon (Excel default in some regions)
    print("\nTest 2: Latin-1 Semicolon")
    with open('test_latin1.csv', 'w', encoding='latin-1') as f:
        f.write("palavra-chave;outra\nCafé;valor\nAção;valor")
    
    try:
        k = read_keywords_from_file(MockBatchJob('test_latin1.csv'))
        print(f"Result: {k}")
        assert "Café" in k
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
        
    # 3. Test No Header
    print("\nTest 3: No Header (Auto-detect first col)")
    with open('test_noheader.csv', 'w', encoding='utf-8') as f:
        f.write("Just a keyword\nAnother keyword")
    
    try:
        k = read_keywords_from_file(MockBatchJob('test_noheader.csv'))
        print(f"Result: {k}")
        assert "Just a keyword" in k
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")

    # Cleanup
    try:
        os.remove('test_utf8.csv')
        os.remove('test_latin1.csv')
        os.remove('test_noheader.csv')
    except:
        pass

if __name__ == "__main__":
    run_tests()
