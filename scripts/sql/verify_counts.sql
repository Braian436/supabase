-- Muestra la cantidad de filas de cada tabla de public.
CREATE TEMP TABLE _conteos (tabla text, filas bigint);

DO $$
DECLARE
    r record;
    c bigint;
BEGIN
    FOR r IN
        SELECT tablename
          FROM pg_tables
         WHERE schemaname = 'public'
         ORDER BY tablename
    LOOP
        EXECUTE format('SELECT count(*) FROM public.%I', r.tablename) INTO c;
        INSERT INTO _conteos VALUES (r.tablename, c);
    END LOOP;
END $$;

SELECT tabla, filas FROM _conteos ORDER BY tabla;
