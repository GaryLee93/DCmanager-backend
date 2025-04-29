# DCmanager-backend

## Database 
1. Install postgresql and connect it (MacOS)
```
brew services start postgresql
psql postgres
```
2. build docker image
```
docker build -t datacenter-postgres .
```
3. run database by docker 
```
docker run -d \
  --name datacenter-db \
  -e POSTGRES_PASSWORD=postgres \
  -v datacenter-db-volume:/var/lib/postgresql/data \
  -p 5433:5432 \
  datacenter-postgres
```
4. connect database (remember to run container first)
```
docker exec -it datacenter-db psql -U postgres -d datacenter_management

```
4. If you want to export current database:
```
pg_dump -d datacenter_management --schema-only > datacenter_db_schema.sql
```



