-- Aditiva. Executar uma vez depois de conferir backup e estrutura atual.
-- Não executar 01_estrutura_base.sql num banco existente.
CREATE TABLE IF NOT EXISTS eventos_publicacao (
 id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
 publicacao_id INT NOT NULL,
 chave_origem VARCHAR(100) NOT NULL,
 dados JSON NOT NULL,
 ativo BOOLEAN NOT NULL DEFAULT TRUE,
 inicio_personalizado VARCHAR(40) NULL,
 nome_personalizado VARCHAR(150) NULL,
 status VARCHAR(20) NOT NULL DEFAULT 'pendente',
 alerta_proximidade INT NULL,
 atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT uq_evento_publicacao_origem UNIQUE (publicacao_id, chave_origem),
 CONSTRAINT fk_eventos_publicacao FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
-- MySQL 8: etapas condicionais para permitir retomada após DDL parcial.
SET @prazus_ddl = (SELECT IF(COUNT(*)=0,
 'ALTER TABLE notificacoes ADD COLUMN evento_id INT NULL', 'SELECT 1')
 FROM information_schema.columns
 WHERE table_schema=DATABASE() AND table_name='notificacoes' AND column_name='evento_id');
PREPARE prazus_stmt FROM @prazus_ddl;
EXECUTE prazus_stmt;
DEALLOCATE PREPARE prazus_stmt;
SET @prazus_ddl = (SELECT IF(COUNT(*)=0,
 'ALTER TABLE notificacoes ADD CONSTRAINT fk_notificacoes_evento FOREIGN KEY (evento_id) REFERENCES eventos_publicacao(id)', 'SELECT 1')
 FROM information_schema.table_constraints
 WHERE constraint_schema=DATABASE() AND table_name='notificacoes' AND constraint_name='fk_notificacoes_evento');
PREPARE prazus_stmt FROM @prazus_ddl;
EXECUTE prazus_stmt;
DEALLOCATE PREPARE prazus_stmt;
