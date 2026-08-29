import unittest
from unittest.mock import patch

from user import User


class CadastroConfirmacaoTests(unittest.TestCase):
    @patch("user.enviar_email_codigo_confirmacao")
    def test_gerar_codigo_confirmacao_envia_email(self, mock_email):
        usuario = User()
        codigo = usuario.gerar_codigo_confirmacao("joao@teste.com")

        self.assertEqual(len(codigo), 4)
        self.assertEqual(usuario.codigo_confirmacao, codigo)
        mock_email.assert_called_once_with("joao@teste.com", codigo)

    def test_validar_codigo_cadastro_limita_duas_tentativas(self):
        usuario = User()
        usuario.codigo_confirmacao = "1234"
        usuario.tentativas_codigo = 0

        self.assertFalse(usuario.validar_codigo_cadastro("0000"))
        self.assertTrue(usuario.validar_codigo_cadastro("1234"))
        self.assertEqual(usuario.tentativas_codigo, 0)

        usuario.codigo_confirmacao = "4321"
        usuario.tentativas_codigo = 0
        self.assertFalse(usuario.validar_codigo_cadastro("1111"))
        self.assertFalse(usuario.validar_codigo_cadastro("2222"))
        self.assertEqual(usuario.tentativas_codigo, 2)


if __name__ == "__main__":
    unittest.main()
