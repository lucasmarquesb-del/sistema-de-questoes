-- Migration: Adicionar campos para imagens remotas
-- Versão: 002
-- Data: 2026-02-05

-- Adicionar colunas à tabela imagem
ALTER TABLE imagem ADD COLUMN url_remota VARCHAR(1000);
ALTER TABLE imagem ADD COLUMN servico_hospedagem VARCHAR(50);
ALTER TABLE imagem ADD COLUMN id_remoto VARCHAR(255);
ALTER TABLE imagem ADD COLUMN url_thumbnail VARCHAR(1000);
ALTER TABLE imagem ADD COLUMN data_upload_remoto DATETIME;

-- Índice para busca por URL (performance)
CREATE INDEX IF NOT EXISTS idx_imagem_url_remota ON imagem(url_remota);
CREATE INDEX IF NOT EXISTS idx_imagem_servico ON imagem(servico_hospedagem);
