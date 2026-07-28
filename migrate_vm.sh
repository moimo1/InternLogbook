#!/bin/bash
echo "Preparing database (Dropping existing schema)..."
docker exec attendance_postgres psql -U admin -d attendance_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO admin; GRANT ALL ON SCHEMA public TO public;"

echo "Importing production_migrate.sql..."
docker exec -i attendance_postgres psql -U admin -d attendance_db < production_migrate.sql

echo "Restarting web container..."
docker restart attendance_web

echo "Migration complete!"
