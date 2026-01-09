#!/usr/bin/env python
"""
Diagnóstico de Jobs CSV Falhados
Executa no servidor para identificar a causa do erro.
"""

import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.automation.models import BatchJob
from django.conf import settings

def diagnose():
    print("=" * 60)
    print("DIAGNÓSTICO DE JOBS CSV")
    print("=" * 60)
    
    # 1. Verificar configuração de media
    print(f"\n[1] MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"    MEDIA_ROOT exists: {os.path.exists(settings.MEDIA_ROOT)}")
    if os.path.exists(settings.MEDIA_ROOT):
        contents = os.listdir(settings.MEDIA_ROOT)
        print(f"    Contents: {contents}")
    
    # 2. Verificar batch_uploads
    batch_uploads_path = os.path.join(settings.MEDIA_ROOT, 'batch_uploads')
    print(f"\n[2] Batch Uploads Path: {batch_uploads_path}")
    print(f"    Path exists: {os.path.exists(batch_uploads_path)}")
    if os.path.exists(batch_uploads_path):
        files = os.listdir(batch_uploads_path)
        print(f"    Files ({len(files)}): {files[:10]}...")
    
    # 3. Listar últimos jobs
    print("\n[3] ÚLTIMOS 10 BATCH JOBS:")
    print("-" * 60)
    
    jobs = BatchJob.objects.all().order_by('-created_at')[:10]
    
    for job in jobs:
        print(f"\nJob ID: {job.id}")
        print(f"  Original Filename: {job.original_filename}")
        print(f"  Status: {job.status}")
        print(f"  Progress: {job.processed_rows}/{job.total_rows}")
        print(f"  Created: {job.created_at}")
        
        if job.csv_file:
            print(f"  CSV File Field: {job.csv_file}")
            print(f"  CSV File Path: {job.csv_file.path}")
            file_exists = os.path.exists(job.csv_file.path)
            print(f"  File Exists: {file_exists}")
            
            if file_exists:
                file_size = os.path.getsize(job.csv_file.path)
                print(f"  File Size: {file_size} bytes")
                
                # Try reading first lines
                try:
                    with open(job.csv_file.path, 'r', encoding='utf-8') as f:
                        content = f.read(500)
                        print(f"  File Preview:\n{content[:200]}")
                except Exception as e:
                    print(f"  Error reading file: {e}")
        else:
            print(f"  CSV File: None")
        
        if job.error_log:
            print(f"  Error Log: {job.error_log}")
    
    # 4. Verificar Redis/Celery
    print("\n[4] CELERY CONFIG:")
    print(f"    BROKER_URL: {settings.CELERY_BROKER_URL}")
    print(f"    RESULT_BACKEND: {getattr(settings, 'CELERY_RESULT_BACKEND', 'Not set')}")
    
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO COMPLETO")
    print("=" * 60)

if __name__ == "__main__":
    diagnose()
