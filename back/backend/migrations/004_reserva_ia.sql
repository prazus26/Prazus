-- Executar APENAS após backup e DESCRIBE analises_ia.
-- Migração ADITIVA para a tabela 003 já criada. Não mexe nos prazos.
-- O serviço exige estas duas colunas para evitar conclusão por outro worker.
ALTER TABLE analises_ia
  ADD COLUMN reserva_token CHAR(32) NULL,
  ADD COLUMN reserva_expira_em DATETIME NULL;

CREATE INDEX idx_analises_ia_reserva
  ON analises_ia (estado, reserva_expira_em);

-- @block
DESCRIBE analises_ia;