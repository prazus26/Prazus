-- Executar uma única vez, no banco prazus_db.
-- Não altera a tabela de prazos.

ALTER TABLE metadados_comunicacao_djen
ADD COLUMN advogado_destinatario JSON NULL;