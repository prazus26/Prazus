
-- ==========================================
-- PRAZUS - BANCO LOCAL DE DESENVOLVIMENTO
-- ==========================================

-- Cria o banco caso ainda não exista
CREATE DATABASE IF NOT EXISTS prazus_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- Cria um usuário local para o Prazus
-- IMPORTANTE:
-- Cada integrante deve substituir a senha
-- abaixo por uma senha própria e privada.

CREATE USER IF NOT EXISTS 'prazus_dev'@'localhost'
IDENTIFIED BY 'SUBSTITUIR_POR_SENHA_LOCAL';

-- Permite acesso apenas ao banco do Prazus
GRANT ALL PRIVILEGES
ON prazus_db.*
TO 'prazus_dev'@'localhost';
