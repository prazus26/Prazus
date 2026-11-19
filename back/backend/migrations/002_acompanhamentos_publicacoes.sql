-- Fase 2: migração aditiva. Execute no banco prazus_db apenas após backup completo.
-- Não toca prazos, publicações ou notificações existentes.
-- Confirme que a tabela não existe antes de executar para evitar divergência de esquema.
USE prazus_db;

CREATE TABLE IF NOT EXISTS acompanhamentos_publicacoes (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    publicacao_id INT NOT NULL,
    estado ENUM('pendente', 'revisada', 'dispensada') NOT NULL DEFAULT 'pendente',
    dias_sugeridos INT NULL,
    tipo_contagem_sugerida VARCHAR(10) NULL,
    trecho_sugerido TEXT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_acompanhamentos_publicacao UNIQUE (publicacao_id),
    CONSTRAINT fk_acompanhamentos_publicacao FOREIGN KEY (publicacao_id)
        REFERENCES publicacoes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- A rotina gera acompanhamentos de todas as publicações idempotentemente.
-- Não é necessário nem desejado migrar os valores legados de 'prazos' automaticamente.

-- Permite registrar a origem MANUAL (não representa extração automática DJEN).
-- Operação de esquema; não altera os valores das linhas existentes.
ALTER TABLE prazos
    MODIFY COLUMN origem_prazo ENUM('djen','estimativa_prazus','manual') NOT NULL;


-- @block
SHOW COLUMNS FROM prazos LIKE 'origem_prazo';