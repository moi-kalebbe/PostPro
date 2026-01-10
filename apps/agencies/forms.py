# apps/agencies/forms.py

from django import forms
from .models import Agency
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

class AgencyBrandingForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = [
            'display_name',
            'logo_light',
            'logo_dark',
            'logo_dark',
            'favicon'
        ]
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nome da sua empresa'
            }),
            'logo_light': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/png,image/jpeg,image/svg+xml,image/webp'
            }),
            'logo_dark': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/png,image/jpeg,image/svg+xml,image/webp'
            }),
            'favicon': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/png,image/x-icon'
            }),
        }
    
    def clean_logo_light(self):
        """Valida e otimiza logo light"""
        logo = self.cleaned_data.get('logo_light')
        
        if logo:
            if hasattr(logo, 'image'): # If it's already an image object from previous save
                return logo
                
            try:
                # Valida dimensões (recomendado: 200x50)
                img = Image.open(logo)
                
                if img.width > 400 or img.height > 100:
                    # Redimensiona mantendo proporção
                    img.thumbnail((400, 100), Image.Resampling.LANCZOS)
                    
                    # Salva otimizado
                    output = BytesIO()
                    # Preserve format if possible, default to PNG
                    fmt = img.format if img.format else 'PNG'
                    img.save(output, format=fmt, optimize=True)
                    output.seek(0)
                    
                    filename = logo.name
                    logo = InMemoryUploadedFile(
                        output, 'ImageField', filename,
                        f'image/{fmt.lower()}', sys.getsizeof(output), None
                    )
            except Exception as e:
                # If PIL fails (e.g. SVG), return as is or handle error
                # For now we just pass through if not processable by PIL (like SVG)
                pass
        
        return logo
    
    def clean_logo_dark(self):
        """Valida e otimiza logo dark"""
        logo = self.cleaned_data.get('logo_dark')
        
        if logo:
            if hasattr(logo, 'image'):
                return logo
                
            try:
                img = Image.open(logo)
                
                if img.width > 400 or img.height > 100:
                    img.thumbnail((400, 100), Image.Resampling.LANCZOS)
                    
                    output = BytesIO()
                    fmt = img.format if img.format else 'PNG'
                    img.save(output, format=fmt, optimize=True)
                    output.seek(0)
                    
                    logo = InMemoryUploadedFile(
                        output, 'ImageField', logo.name,
                        f'image/{fmt.lower()}', sys.getsizeof(output), None
                    )
            except Exception:
                pass
        
        return logo
    
    def clean_favicon(self):
        """Valida favicon (deve ser 32x32 ou 64x64)"""
        favicon = self.cleaned_data.get('favicon')
        
        if favicon:
            if hasattr(favicon, 'image'):
                return favicon
                
            try:
                img = Image.open(favicon)
                
                # Redimensiona para 32x32 se necessário
                if img.size != (32, 32) and img.size != (64, 64):
                    img = img.resize((32, 32), Image.Resampling.LANCZOS)
                    
                    output = BytesIO()
                    img.save(output, format='PNG')
                    output.seek(0)
                    
                    name_parts = favicon.name.split('.')
                    new_name = f"{'.'.join(name_parts[:-1])}.png"
                    
                    favicon = InMemoryUploadedFile(
                        output, 'ImageField', new_name,
                        'image/png', sys.getsizeof(output), None
                    )
            except Exception:
                pass
        
        return favicon
