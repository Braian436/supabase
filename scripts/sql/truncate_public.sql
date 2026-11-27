-- Borra los datos de todas las tablas de public menos django_migrations.
-- Se ejecuta dentro de la transaccion de importacion, antes del COPY.
-- El CASCADE arrastra las tablas dependientes; django_migrations no tiene FKs.
DO $$
DECLARE
    lista text;
BEGIN
    SELECT string_agg(format('%I.%I', schemaname, tablename), ', ')
      INTO lista
      FROM pg_tables
     WHERE schemaname = 'public'
       AND tablename <> 'django_migrations';

    IF lista IS NOT NULL THEN
        EXECUTE 'TRUNCATE TABLE ' || lista || ' RESTART IDENTITY CASCADE';
    END IF;
END $$;
