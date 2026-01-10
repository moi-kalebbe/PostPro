# PostPro WordPress Plugin

> ⚠️ **IMPORTANTE: NÃO ALTERE O DESIGN DESTE PLUGIN!**

Este plugin tem um design específico aprovado pelo cliente. O design atual é considerado FINAL e não deve ser modificado sem aprovação explícita.

## Versão Atual
- **Versão**: 2.2.0
- **Design aprovado em**: 09/01/2026 às 18:14

## Estrutura
```
postpro/
├── postpro.php          # Arquivo principal do plugin
└── assets/
    ├── css/
    │   └── admin.css    # CSS DO PLUGIN - NÃO ALTERAR DESIGN!
    └── js/
        └── admin.js     # JavaScript do plugin
```

## Regras de Desenvolvimento

### ✅ O que PODE ser alterado:
- Correção de bugs de funcionalidade
- URL da API (`POSTPRO_API_BASE`)
- Lógica de comunicação com backend
- Número da versão

### ❌ O que NÃO PODE ser alterado:
- Layout visual (CSS)
- Estrutura HTML dos componentes
- Cores, fontes, espaçamentos
- Estilo dos cards, botões, tabelas

## API URL
A URL da API deve apontar para:
```
https://postpro.nuvemchat.com/api/v1
```

## Como criar o ZIP para distribuição
```powershell
Compress-Archive -Path "wordpress-plugin\postpro" -DestinationPath "postpro-v2.2.0.zip"
```
