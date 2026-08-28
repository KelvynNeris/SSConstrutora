-- Criar banco de dados
CREATE DATABASE bd_ws;
USE bd_ws;

-- Tabela de usuários (administrador e funcionários)
CREATE TABLE tb_usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    telefone VARCHAR(15),
    tipo_usuario ENUM('Administrador', 'Funcionario') NOT NULL,
    codigo_confirmacao CHAR(4) NOT NULL, -- Código de 4 dígitos para confirmação de entrega
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    primeiro_login BOOLEAN DEFAULT TRUE
);

-- Tabela de materiais/produtos
CREATE TABLE tb_materiais (
    id_material INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    unidade VARCHAR(20) DEFAULT 'unidade', -- Ex: unidade, caixa, kg, etc.
    quantidade_estoque DECIMAL(10,2) DEFAULT 0 NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de pedidos de materiais feitos pelos funcionários
CREATE TABLE tb_pedidos (
    id_pedido INT AUTO_INCREMENT PRIMARY KEY,
    id_funcionario INT NOT NULL,
    id_material INT NOT NULL,
    quantidade DECIMAL(10,2) NOT NULL,
    status ENUM('Pendente', 'Aprovado', 'Recusado', 'Atendido') DEFAULT 'Pendente',
    data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_resposta TIMESTAMP NULL,
    observacao_admin TEXT,
    FOREIGN KEY (id_funcionario) REFERENCES tb_usuarios(id_usuario),
    FOREIGN KEY (id_material) REFERENCES tb_materiais(id_material)
);

-- Usuário administrador inicial (exemplo de código: 1234)
INSERT INTO tb_usuarios (nome, email, senha, telefone, tipo_usuario, codigo_confirmacao, primeiro_login)
VALUES ('Administrador Master', 'adm@adm.com', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', '123456789', 'Administrador', '1234', TRUE);

-- Exemplo de material inicial
INSERT INTO tb_materiais (nome, descricao, unidade, quantidade_estoque)
VALUES ('Prego', 'Prego comum para construção civil', 'unidade', 1000);