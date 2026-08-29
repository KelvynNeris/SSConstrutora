-- Tabela para tokens de recuperação de senha
ALTER TABLE tb_usuarios ADD COLUMN IF NOT EXISTS token_reset_senha VARCHAR(255) NULL;
ALTER TABLE tb_usuarios ADD COLUMN IF NOT EXISTS token_reset_expiracao DATETIME NULL;

-- Tabela de log de auditoria
CREATE TABLE IF NOT EXISTS tb_auditoria (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    acao VARCHAR(100) NOT NULL,
    descricao TEXT,
    endereco_ip VARCHAR(45),
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES tb_usuarios(id_usuario) ON DELETE CASCADE,
    INDEX idx_usuario_data (id_usuario, data_hora)
);

-- Tabela de tentativas de login falhadas (para análise de segurança)
CREATE TABLE IF NOT EXISTS tb_tentativas_login (
    id_tentativa INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    endereco_ip VARCHAR(45),
    sucesso BOOLEAN,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email_data (email, data_hora)
);
