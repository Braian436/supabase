-- Ajusta cada secuencia al maximo id real de su tabla.
-- Necesario porque los nombres de secuencia de Supabase no siempre coinciden
-- con los que genera Django (por ejemplo categorias_id_seq vs
-- categorias_id_categoria_seq, o ventas_id_ventas_seq vs ventas_id_venta_seq).
DO $$
DECLARE
    r record;
    seq text;
    max_id bigint;
BEGIN
    FOR r IN
        SELECT n.nspname AS schema_name,
               c.relname AS table_name,
               a.attname AS column_name
          FROM pg_class c
          JOIN pg_namespace n ON n.oid = c.relnamespace
          JOIN pg_index i ON i.indrelid = c.oid AND i.indisprimary
          JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = i.indkey[0]
         WHERE n.nspname = 'public'
           AND c.relkind = 'r'
           AND i.indnatts = 1
           AND a.atttypid IN ('int2'::regtype, 'int4'::regtype, 'int8'::regtype)
    LOOP
        seq := pg_get_serial_sequence(
            format('%I.%I', r.schema_name, r.table_name),
            r.column_name
        );

        IF seq IS NOT NULL THEN
            EXECUTE format(
                'SELECT COALESCE(max(%I), 0) FROM %I.%I',
                r.column_name, r.schema_name, r.table_name
            ) INTO max_id;

            IF max_id > 0 THEN
                PERFORM setval(seq, max_id, true);
            ELSE
                PERFORM setval(seq, 1, false);
            END IF;
        END IF;
    END LOOP;
END $$;
