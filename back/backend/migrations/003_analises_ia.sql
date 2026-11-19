-- Prazus / Gemini: etapa inicial de persistencia (MySQL 8)
-- Adiciona exclusivamente a tabela de controle das analises de IA.
-- Nao altera: prazos, publicacoes, acompanhamentos, processos, notificacoes.
-- Conferir SELECT DATABASE() antes de executar.

CREATE TABLE analises_ia (
    id INT NOT NULL AUTO_INCREMENT,
    publicacao_id INT NOT NULL,
    hash_conteudo CHAR(64) NOT NULL,
    versao_analisador VARCHAR(30) NOT NULL,
    modelo_ia VARCHAR(100) NOT NULL,
    estado ENUM('pendente','processando','concluida','falha','aguardando_cota') NOT NULL DEFAULT 'pendente',
    resultado_json JSON NULL,
    tentativas INT NOT NULL DEFAULT 0,
    proxima_tentativa_em DATETIME NULL,
    erro_resumido VARCHAR(500) NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    analisado_em DATETIME NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_analises_ia_versao UNIQUE (publicacao_id, hash_conteudo, versao_analisador),
    CONSTRAINT fk_analises_ia_publicacao FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id),
    INDEX idx_analises_ia_fila (estado, proxima_tentativa_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
