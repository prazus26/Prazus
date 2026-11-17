-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: prazus_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `acompanhamentos_publicacoes`
--

DROP TABLE IF EXISTS `acompanhamentos_publicacoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `acompanhamentos_publicacoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `publicacao_id` int NOT NULL,
  `estado` enum('pendente','revisada','dispensada') NOT NULL DEFAULT 'pendente',
  `dias_sugeridos` int DEFAULT NULL,
  `tipo_contagem_sugerida` varchar(10) DEFAULT NULL,
  `trecho_sugerido` text,
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_acompanhamentos_publicacao` (`publicacao_id`),
  CONSTRAINT `fk_acompanhamentos_publicacao` FOREIGN KEY (`publicacao_id`) REFERENCES `publicacoes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=138 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `analises_ia`
--

DROP TABLE IF EXISTS `analises_ia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `analises_ia` (
  `id` int NOT NULL AUTO_INCREMENT,
  `publicacao_id` int NOT NULL,
  `hash_conteudo` char(64) NOT NULL,
  `versao_analisador` varchar(30) NOT NULL,
  `modelo_ia` varchar(100) NOT NULL,
  `estado` enum('pendente','processando','concluida','falha','aguardando_cota') NOT NULL DEFAULT 'pendente',
  `resultado_json` json DEFAULT NULL,
  `tentativas` int NOT NULL DEFAULT '0',
  `proxima_tentativa_em` datetime DEFAULT NULL,
  `erro_resumido` varchar(500) DEFAULT NULL,
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `analisado_em` datetime DEFAULT NULL,
  `reserva_token` char(32) DEFAULT NULL,
  `reserva_expira_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_analises_ia_versao` (`publicacao_id`,`hash_conteudo`,`versao_analisador`),
  KEY `idx_analises_ia_fila` (`estado`,`proxima_tentativa_em`),
  KEY `idx_analises_ia_reserva` (`estado`,`reserva_expira_em`),
  CONSTRAINT `fk_analises_ia_publicacao` FOREIGN KEY (`publicacao_id`) REFERENCES `publicacoes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `apscheduler_jobs`
--

DROP TABLE IF EXISTS `apscheduler_jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `apscheduler_jobs` (
  `id` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `next_run_time` double DEFAULT NULL,
  `job_state` blob NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_apscheduler_jobs_next_run_time` (`next_run_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `configuracoes_usuario`
--

DROP TABLE IF EXISTS `configuracoes_usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuracoes_usuario` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `escala_cores` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `limite_urgente` int NOT NULL DEFAULT '3',
  `limite_atencao` int NOT NULL DEFAULT '7',
  `cor_vencido` varchar(7) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '#FF8C69',
  `cor_urgente` varchar(7) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '#FCBF69',
  `cor_atencao` varchar(7) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '#F3E27A',
  `cor_tranquilo` varchar(7) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '#ADF3A0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `fk_configuracoes_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cota_ia_diaria`
--

DROP TABLE IF EXISTS `cota_ia_diaria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cota_ia_diaria` (
  `dia` date NOT NULL,
  `tentativas_iniciadas` int NOT NULL DEFAULT '0',
  `atualizado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`dia`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `feriados`
--

DROP TABLE IF EXISTS `feriados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feriados` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `data` date NOT NULL,
  `abrangencia` enum('nacional','estadual','municipal') COLLATE utf8mb4_unicode_ci NOT NULL,
  `uf` char(2) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `municipio` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_feriados_data` (`data`),
  KEY `idx_feriados_local` (`abrangencia`,`uf`,`municipio`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `historico_alteracoes`
--

DROP TABLE IF EXISTS `historico_alteracoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historico_alteracoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `tipo_registro` enum('processo','publicacao','prazo') COLLATE utf8mb4_unicode_ci NOT NULL,
  `registro_id` int NOT NULL,
  `campo_alterado` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valor_anterior` json DEFAULT NULL,
  `valor_novo` json DEFAULT NULL,
  `alterado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_alteracoes_registro` (`tipo_registro`,`registro_id`),
  KEY `idx_alteracoes_usuario_data` (`usuario_id`,`alterado_em`),
  CONSTRAINT `fk_alteracoes_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `historico_execucoes`
--

DROP TABLE IF EXISTS `historico_execucoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historico_execucoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `inicio_execucao` datetime NOT NULL,
  `fim_execucao` datetime DEFAULT NULL,
  `status` enum('executando','sucesso','erro') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'executando',
  `quantidade_publicacoes` int NOT NULL DEFAULT '0',
  `mensagem_erro` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `fk_execucoes_usuario` (`usuario_id`),
  KEY `idx_execucoes_inicio` (`inicio_execucao`),
  KEY `idx_execucoes_status` (`status`),
  CONSTRAINT `fk_execucoes_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `metadados_comunicacao_djen`
--

DROP TABLE IF EXISTS `metadados_comunicacao_djen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `metadados_comunicacao_djen` (
  `id` int NOT NULL AUTO_INCREMENT,
  `publicacao_id` int NOT NULL,
  `tipo_comunicacao` varchar(150) DEFAULT NULL,
  `meio` varchar(150) DEFAULT NULL,
  `status_djen` varchar(150) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `data_cancelamento` date DEFAULT NULL,
  `nome_orgao` varchar(255) DEFAULT NULL,
  `id_orgao` varchar(100) DEFAULT NULL,
  `atualizado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `advogado_destinatario` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_metadados_djen_publicacao` (`publicacao_id`),
  CONSTRAINT `fk_metadados_djen_publicacao` FOREIGN KEY (`publicacao_id`) REFERENCES `publicacoes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=116 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notificacoes`
--

DROP TABLE IF EXISTS `notificacoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notificacoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `prazo_id` int DEFAULT NULL,
  `chave_evento` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `titulo` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `mensagem` text COLLATE utf8mb4_unicode_ci,
  `data_notificacao` datetime NOT NULL,
  `visualizada` tinyint(1) NOT NULL DEFAULT '0',
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_notificacao_evento` (`usuario_id`,`chave_evento`),
  KEY `fk_notificacoes_prazo` (`prazo_id`),
  KEY `idx_notificacoes_data` (`usuario_id`,`data_notificacao`),
  KEY `idx_notificacoes_visualizada` (`usuario_id`,`visualizada`),
  CONSTRAINT `fk_notificacoes_prazo` FOREIGN KEY (`prazo_id`) REFERENCES `prazos` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_notificacoes_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `prazos`
--

DROP TABLE IF EXISTS `prazos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prazos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `publicacao_id` int NOT NULL,
  `dias_prazo_original` int DEFAULT NULL,
  `dias_prazo_atual` int DEFAULT NULL,
  `tipo_contagem_original` enum('corridos','uteis') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tipo_contagem_atual` enum('corridos','uteis') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'corridos',
  `data_inicio_original` date DEFAULT NULL,
  `data_inicio_atual` date DEFAULT NULL,
  `data_vencimento_original` date DEFAULT NULL,
  `data_vencimento_atual` date DEFAULT NULL,
  `origem_prazo` enum('djen','estimativa_prazus','manual') COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` enum('pendente','concluido','cancelado') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pendente',
  `concluido_em` datetime DEFAULT NULL,
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `nome_prazo` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `alerta_proximidade` int DEFAULT NULL,
  `exibir_calendario` tinyint(1) NOT NULL DEFAULT '0',
  `dias_sugeridos` int DEFAULT NULL,
  `trecho_sugerido` text COLLATE utf8mb4_unicode_ci,
  `revisao_estado` enum('pendente','confirmada','descartada') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `personalizado_manualmente` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `publicacao_id` (`publicacao_id`),
  KEY `idx_prazos_vencimento` (`data_vencimento_atual`),
  KEY `idx_prazos_status` (`status`),
  CONSTRAINT `fk_prazos_publicacao` FOREIGN KEY (`publicacao_id`) REFERENCES `publicacoes` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=250 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `processos`
--

DROP TABLE IF EXISTS `processos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `processos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `numero_processo` varchar(25) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tribunal` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `assunto_original` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `assunto_personalizado` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `classe_original` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `classe_personalizada` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `observacoes_usuario` text COLLATE utf8mb4_unicode_ci,
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  `cliente` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vara` enum('civil','trabalhista','federal') COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `link_processo` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_processo_usuario_numero` (`usuario_id`,`numero_processo`),
  KEY `idx_processos_numero` (`numero_processo`),
  CONSTRAINT `fk_processos_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=110 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `publicacoes`
--

DROP TABLE IF EXISTS `publicacoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `publicacoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `processo_id` int NOT NULL,
  `identificador_djen` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `data_disponibilizacao` date NOT NULL,
  `data_publicacao` date DEFAULT NULL,
  `conteudo_original` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `criado_em` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_publicacao_processo_djen` (`processo_id`,`identificador_djen`),
  KEY `idx_publicacoes_data` (`data_publicacao`),
  KEY `idx_publicacoes_disponibilizacao` (`data_disponibilizacao`),
  CONSTRAINT `fk_publicacoes_processo` FOREIGN KEY (`processo_id`) REFERENCES `processos` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=138 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `senha_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `oab_numero` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `oab_uf` varchar(2) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-16 21:24:11
