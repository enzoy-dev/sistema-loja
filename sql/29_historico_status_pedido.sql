CREATE TABLE historico_status_pedido (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pedido_id INTEGER NOT NULL,
    status_anterior VARCHAR(30),
    status_novo VARCHAR(30) NOT NULL,
    data_alteracao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_historico_pedido
        FOREIGN KEY (pedido_id)
        REFERENCES pedidos(id)
);


CREATE OR REPLACE FUNCTION registrar_historico_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF OLD.status IS DISTINCT FROM NEW.status THEN

        INSERT INTO historico_status_pedido (
            pedido_id,
            status_anterior,
            status_novo
        )
        VALUES (
            NEW.id,
            OLD.status,
            NEW.status
        );

    END IF;

    RETURN NEW;

END;
$$;


CREATE TRIGGER trigger_historico_status
AFTER UPDATE OF status ON pedidos
FOR EACH ROW
EXECUTE FUNCTION registrar_historico_status();