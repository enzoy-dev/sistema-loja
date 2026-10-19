import shutil
import subprocess


def test_setup_failure_leaves_no_partial_schema(connection, test_database, tmp_path):
    from conftest import ROOT

    # Somente o banco temporário dos testes é alterado.
    connection.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public')
    target = tmp_path / 'sql'
    shutil.copytree(ROOT / 'sql', target)
    with (target / '02_inserts.sql').open('a') as seed:
        seed.write("\nDO $$ BEGIN RAISE EXCEPTION 'Falha simulada no setup'; END; $$;\n")
    result = subprocess.run(
        ['psql', '-X', '-d', test_database, '-f', str(target / '00_setup.sql')],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0
    assert 'Falha simulada no setup' in result.stderr
    assert 'Setup finalizado com sucesso' not in result.stdout
    assert connection.execute("SELECT count(*) AS n FROM information_schema.tables WHERE table_schema='public'").fetchone()['n'] == 0
