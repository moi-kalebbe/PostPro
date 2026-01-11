-- Verificar modelo atual da agência
SELECT id, name, default_text_model FROM agencies;

-- Atualizar para deepseek-chat
UPDATE agencies 
SET default_text_model = 'deepseek/deepseek-chat' 
WHERE default_text_model = 'deepseek/deepseek-v3';

-- Verificar
SELECT id, name, default_text_model FROM agencies;
