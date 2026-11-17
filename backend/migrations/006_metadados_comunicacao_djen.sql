-- Prazus: migration 006 (ADITIVA)
-- Preserva publicacoes, prazos, analises_ia, acompanhamentos_publicacoes.
-- Execute uma vez em prazus_db depois de fazer backup.
CREATE TABLE metadados_comunicacao_djen (
    id INT NOT NULL AUTO_INCREMENT,
    publicacao_id INT NOT NULL,
    tipo_comunicacao VARCHAR(150) NULL,
    meio VARCHAR(150) NULL,
    status_djen VARCHAR(150) NULL,
    ativo TINYINT(1) NULL,
    data_cancelamento DATE NULL,
    nome_orgao VARCHAR(255) NULL,
    id_orgao VARCHAR(100) NULL,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_metadados_djen_publicacao (publicacao_id),
    CONSTRAINT fk_metadados_djen_publicacao
      FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- @block
SELECT COUNT(*) AS total
FROM metadados_comunicacao_djen;