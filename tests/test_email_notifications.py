import unittest
from unittest.mock import patch, MagicMock

from adm import Administrador


class EmailNotificationsTests(unittest.TestCase):
    @patch("adm.enviar_email_funcionario")
    @patch("adm.Conexao.conectar")
    def test_atualizar_requisicao_envia_email_ao_funcionario(self, mock_conectar, mock_email):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_conectar.return_value = mock_conn

        mock_cursor.fetchone.side_effect = [
            ("Maria", "maria@teste.com", "Obra Teste", "Cimento", 10, "saco"),
        ]

        resultado = Administrador.atualizar_requisicao(
            id_pedido=10,
            id_administrador=1,
            status="Aprovado",
            valor_pago="150,50",
            loja="Loja Teste",
        )

        self.assertTrue(resultado)
        mock_email.assert_called_once()


if __name__ == "__main__":
    unittest.main()
