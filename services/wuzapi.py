"""
Wuzapi Service for PostPro.
WhatsApp integration via Wuzapi API.
"""

import re
import secrets
import requests
from django.conf import settings
from django.utils import timezone


class WuzapiService:
    """Serviço para integração com API Wuzapi (WhatsApp)"""
    
    def __init__(self, agency):
        self.agency = agency
        self.base_url = agency.wuzapi_instance_url.rstrip('/')
        self.token = agency.wuzapi_token
        self.admin_token = getattr(settings, 'WUZAPI_ADMIN_TOKEN', '')
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida formato de telefone brasileiro."""
        if not phone:
            return False
        cleaned = re.sub(r'\D', '', phone)
        # 10-11 dígitos (com DDD) ou 12-13 (com código país)
        return 10 <= len(cleaned) <= 13
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """Formata telefone para padrão internacional (5519999999999)."""
        if not phone:
            return ''
        cleaned = re.sub(r'\D', '', phone)
        
        # Remove 0 inicial do DDD se houver
        if cleaned.startswith('0'):
            cleaned = cleaned[1:]
        
        # Adiciona código do país se não tiver
        if not cleaned.startswith('55'):
            cleaned = '55' + cleaned
        
        return cleaned
    
    def _request(self, method: str, endpoint: str, data: dict = None, use_admin: bool = False) -> dict:
        """Faz requisição à API Wuzapi."""
        url = f"{self.base_url}{endpoint}"
        # Wuzapi API uses 'Token' header for user endpoints, 'Authorization' for admin
        if use_admin:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': self.admin_token
            }
        else:
            headers = {
                'Content-Type': 'application/json',
                'Token': self.token
            }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data or {}, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return {'success': False, 'message': f'Método {method} não suportado'}
            
            if response.status_code >= 400:
                return {
                    'success': False,
                    'message': f'Erro HTTP {response.status_code}',
                    'data': response.json() if response.text else {}
                }
            
            return {
                'success': True,
                'data': response.json() if response.text else {}
            }
            
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Timeout na requisição'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'message': str(e)}
        except Exception as e:
            return {'success': False, 'message': f'Erro inesperado: {str(e)}'}
    
    def create_wuzapi_user(self) -> dict:
        """Cria usuário Wuzapi para a agência."""
        token = secrets.token_hex(32)
        site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        webhook_url = f"{site_url}/api/v1/webhook/wuzapi/{self.agency.id}/"
        
        result = self._request('POST', '/admin/users', {
            'name': f'agency_{self.agency.id}',
            'token': token,
            'webhook': webhook_url,
            'events': 'Message,ReadReceipt'
        }, use_admin=True)
        
        if result['success']:
            self.agency.wuzapi_user_id = result['data'].get('id')
            self.agency.wuzapi_token = token
            self.agency.save(update_fields=['wuzapi_user_id', 'wuzapi_token'])
            self.token = token
        
        return result
    
    def delete_wuzapi_user(self) -> dict:
        """Remove usuário Wuzapi da agência."""
        if not self.agency.wuzapi_user_id:
            return {'success': False, 'message': 'Usuário não existe'}
        
        result = self._request(
            'DELETE', 
            f'/admin/users/{self.agency.wuzapi_user_id}',
            use_admin=True
        )
        
        if result['success']:
            self.agency.wuzapi_user_id = None
            self.agency.wuzapi_token = ''
            self.agency.wuzapi_phone = ''
            self.agency.wuzapi_connected = False
            self.agency.wuzapi_connected_at = None
            self.agency.save()
        
        return result
    
    def connect(self) -> dict:
        """Inicia conexão WhatsApp."""
        return self._request('POST', '/session/connect', {
            'Subscribe': ['Message'],
            'Immediate': False
        })
    
    def get_qr_code(self) -> dict:
        """Obtém QR Code para conexão."""
        result = self._request('GET', '/session/qr')
        
        if result['success']:
            data = result.get('data', {})
            qr_data = data.get('data', data)
            qr_code = qr_data.get('QRCode', '')
            
            if qr_code:
                return {'success': True, 'qr_code': qr_code}
        
        return {'success': False, 'message': 'QR Code não disponível'}
    
    def get_status(self) -> dict:
        """Verifica status da conexão."""
        result = self._request('GET', '/session/status')
        
        if result['success']:
            data = result.get('data', {})
            status_data = data.get('data', data)
            # Try PascalCase (docs) and camelCase (actual response)
            is_connected = status_data.get('Connected') or status_data.get('connected') or False
            is_logged_in = status_data.get('LoggedIn') or status_data.get('loggedIn') or False
            
            connected = bool(is_connected and is_logged_in)
            
            # Atualiza status na agência
            if connected != self.agency.wuzapi_connected:
                self.agency.wuzapi_connected = connected
                if connected:
                    self.agency.wuzapi_connected_at = timezone.now()
                self.agency.save(update_fields=['wuzapi_connected', 'wuzapi_connected_at'])
            
            return {
                'success': True,
                'connected': connected,
                'logged_in': status_data.get('LoggedIn', False)
            }
        
        return result
    
    def disconnect(self) -> dict:
        """Desconecta WhatsApp."""
        # Endpoint correto é /session/logout e não /session/disconnect
        result = self._request('POST', '/session/logout')
        
        # Se retornar erro 'no session', considera como sucesso (já desconectado)
        if not result['success'] and result.get('data') and 'no session' in str(result['data']):
            result = {'success': True, 'message': 'Sessão já desconectada'}
        
        if result['success']:
            self.agency.wuzapi_connected = False
            self.agency.save(update_fields=['wuzapi_connected'])
        
        return result
    
    def send_message(self, phone: str, message: str) -> dict:
        """Envia mensagem de texto."""
        formatted_phone = self.format_phone(phone)
        
        if not formatted_phone:
            return {'success': False, 'message': 'Telefone inválido'}
        
        return self._request('POST', '/chat/send/text', {
            'Phone': formatted_phone,
            'Body': message,
            'LinkPreview': True
        })
    
    def send_project_access(self, project) -> dict:
        """Envia acesso do projeto via WhatsApp."""
        if not self.agency.wuzapi_connected:
            return {'success': False, 'message': 'WhatsApp não conectado'}
        
        if not project.client_phone:
            return {'success': False, 'message': 'Telefone não cadastrado'}
        
        client_name = project.client_name or 'Cliente'
        agency_name = self.agency.get_display_name()
        
        message = f"""🎉 *Olá {client_name}!*

Seu projeto está pronto para instalação!

🌐 *Site:* {project.wordpress_url}

📥 *Link de Instalação:*
{project.get_magic_link_url()}

🔑 *Licença:* `{project.license_key}`

Acesse o link acima para baixar o plugin e ver as instruções de instalação.

Qualquer dúvida, estamos à disposição!

_{agency_name}_"""
        
        result = self.send_message(project.client_phone, message)
        
        if result['success']:
            project.access_sent_at = timezone.now()
            project.access_sent_count += 1
            project.save(update_fields=['access_sent_at', 'access_sent_count'])
        
        return result
