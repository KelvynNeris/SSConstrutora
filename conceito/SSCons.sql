-- Criar banco de dados
CREATE DATABASE bd_ss;
USE bd_ss;

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

-- Obras cadastradas pelo administrador
CREATE TABLE tb_obras (
    id_obra INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    endereco VARCHAR(255) NOT NULL,
    responsavel VARCHAR(100),
    id_administrador INT NOT NULL,
    ativa BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_administrador) REFERENCES tb_usuarios(id_usuario)
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
VALUES ('Administrador Master', 'adm@adm.com', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', '12345678910', 'Administrador', '1234', TRUE);

-- Exemplo de material inicial
INSERT INTO tb_materiais (nome, descricao, unidade, quantidade_estoque)
VALUES ('Prego', 'Prego comum para construção civil', 'unidade', 1000);

-- Campos adicionais para registrar o contexto e o custo real de cada pedido
ALTER TABLE tb_pedidos
    ADD COLUMN obra VARCHAR(150) NULL AFTER id_material,
    ADD COLUMN apresentacao VARCHAR(50) NULL AFTER quantidade,
    ADD COLUMN loja_fornecedora VARCHAR(150) NULL AFTER observacao_admin,
    ADD COLUMN valor_pago DECIMAL(10,2) NULL AFTER loja_fornecedora,
    ADD COLUMN id_administrador INT NULL AFTER valor_pago,
    ADD COLUMN data_pagamento DATETIME NULL AFTER id_administrador,
    ADD CONSTRAINT fk_pedido_administrador
        FOREIGN KEY (id_administrador) REFERENCES tb_usuarios(id_usuario);

    -- Para bancos criados antes da coluna aprovado existir:
    ALTER TABLE tb_usuarios ADD COLUMN aprovado BOOLEAN DEFAULT FALSE;
    UPDATE tb_usuarios
    SET aprovado = TRUE
    WHERE id_usuario > 0 AND tipo_usuario = 'Administrador';

-- Histórico de cotações para o mesmo material em lojas diferentes
CREATE TABLE tb_cotacoes (
    id_cotacao INT AUTO_INCREMENT PRIMARY KEY,
    id_pedido INT NOT NULL,
    loja VARCHAR(150) NOT NULL,
    valor_unitario DECIMAL(10,2) NOT NULL,
    frete DECIMAL(10,2) DEFAULT 0 NOT NULL,
    desconto DECIMAL(10,2) DEFAULT 0 NOT NULL,
    valor_total DECIMAL(10,2) NOT NULL,
    aprovada BOOLEAN DEFAULT FALSE,
    data_cotacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_pedido) REFERENCES tb_pedidos(id_pedido)
);

-- Dados fictícios para testar o sistema
INSERT INTO tb_usuarios
    (nome, email, senha, telefone, tipo_usuario, codigo_confirmacao, primeiro_login, aprovado)
VALUES
    ('Marcos Silva', 'marcos.silva@ssconstrutora.com', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '11987654321', 'Funcionario', '2418', FALSE, TRUE),
    ('Rafael Alves', 'rafael.alves@ssconstrutora.com', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '11976543210', 'Funcionario', '5830', TRUE, TRUE),
    ('João Costa', 'joao.costa@ssconstrutora.com', '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', '11965432109', 'Funcionario', '7194', TRUE, FALSE);

INSERT INTO tb_materiais (nome, descricao, unidade, quantidade_estoque)
VALUES
    ('Cimento CP-II', 'Cimento para uso geral na construção civil', 'saco', 180),
    ('Tijolo cerâmico', 'Tijolo cerâmico de oito furos', 'unidade', 2500),
    ('Areia média', 'Areia média para argamassa e concreto', 'saco', 320),
    ('Brita 1', 'Agregado graúdo para concreto', 'saco', 150),
    ('Ferro 10 mm', 'Barra de aço para estrutura', 'barra', 95);

INSERT INTO tb_pedidos
    (id_funcionario, id_material, obra, quantidade, apresentacao, status, data_pedido, data_resposta, observacao_admin, loja_fornecedora, valor_pago, id_administrador, data_pagamento)
VALUES
    (2, 2, 'Residencial Jardim Sul', 10, 'saco-50', 'Aprovado', '2026-08-28 08:12:00', '2026-08-28 08:45:00', 'Compra aprovada.', 'Casa do Construtor', 420.00, 1, '2026-08-28 09:00:00'),
    (3, 3, 'Reforma Vila Nova', 500, 'unidade', 'Pendente', '2026-08-27 14:30:00', NULL, NULL, NULL, NULL, NULL, NULL),
    (4, 1, 'Comercial Centro', 15, 'kg', 'Atendido', '2026-08-26 10:05:00', '2026-08-26 13:20:00', 'Material entregue na obra.', 'Constrular', 186.50, 1, '2026-08-26 13:30:00'),
    (2, 4, 'Residencial Jardim Sul', 30, 'saco-25', 'Aprovado', '2026-08-25 16:10:00', '2026-08-25 16:50:00', 'Compra aprovada.', 'Materiais Brasil', 870.00, 1, '2026-08-25 17:00:00');

INSERT INTO tb_cotacoes
    (id_pedido, loja, valor_unitario, frete, desconto, valor_total, aprovada)
VALUES
    (1, 'Casa do Construtor', 42.00, 0.00, 0.00, 420.00, TRUE),
    (1, 'Constrular', 44.50, 25.00, 0.00, 470.00, FALSE),
    (2, 'Materiais Brasil', 2.30, 60.00, 0.00, 1210.00, FALSE),
    (4, 'Materiais Brasil', 29.00, 0.00, 0.00, 870.00, TRUE);