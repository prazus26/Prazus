-- Aditiva; não altera consumo já registrado.
CREATE TABLE IF NOT EXISTS cota_ia_diaria (
 dia DATE PRIMARY KEY,
 tentativas_iniciadas INT NOT NULL DEFAULT 0,
 atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
