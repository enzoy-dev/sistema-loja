"""Administrative account bootstrap/password reset; never seeds a default password."""

import argparse
from getpass import getpass

from api.auth import create_user, hash_password
from api.db import connect_database


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["create-user", "reset-password"])
    parser.add_argument("--login", required=True)
    parser.add_argument(
        "--role", choices=["admin", "vendedor", "leitor"], default="leitor"
    )
    args = parser.parse_args()
    password = getpass("Senha (12 a 128 caracteres): ")
    if not 12 <= len(password) <= 128 or password != getpass("Confirme a senha: "):
        parser.error("Senha inválida ou confirmação diferente")
    with connect_database() as connection:
        if args.action == "create-user":
            create_user(connection, args.login, password, args.role)
        else:
            user = connection.execute(
                "UPDATE usuarios_api SET senha_hash=%s WHERE login=%s RETURNING id",
                (hash_password(password), args.login),
            ).fetchone()
            if user is None:
                parser.error("Usuário não encontrado")
            connection.execute(
                "DELETE FROM sessoes_api WHERE usuario_id=%s", (user["id"],)
            )
            connection.execute(
                "DELETE FROM tentativas_login_api WHERE login=%s", (args.login,)
            )
    print(
        "Conta criada."
        if args.action == "create-user"
        else "Senha atualizada e sessões revogadas."
    )


if __name__ == "__main__":
    main()
