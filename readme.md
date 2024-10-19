## Create Virtual Environment
python -m venv env

## Activate Environment
.\env\Scripts\activate


## Install Requirements
pip install requirements.txt

## To run 
python manage.py runserver

## Console Command
#There are two console command 
1.for creating order everyday for subscription
2.To check the validity of the subscription

## To run these command
Python manage.py create_order
python manage.py check_subscription



## Delete all tables in postgresql 
```sql
do $$ declare
    r record;
begin
    for r in (select tablename from pg_tables where schemaname = 'public') loop
        execute 'drop table if exists ' || quote_ident(r.tablename) || ' cascade';
    end loop;
end $$;
```
