# [Python](https://python.org) script to grab [Cloudflare](https://api.cloudflare.com/#zone-analytics-dashboard) analytics to your own [PostgreSQL](https://postgresql.org) database. 

I use this to populate my [Grafana](https://grafana.org) dashboard with Cloudflare analytics.

# TL;DR
* Install [psycopg2](http://initd.org/psycopg/): ```sudo pip install psycopg2-binary```
* ```cp .env-sample .env``` or set those as environment variables in your shell before running
* Fill in the secrets (or set those as environment variables in your shell before running)
* put it in your crontab: ```@hourly cd ${HOME}/src/cloudflare-analytics-db/ && . .env && sleep $((RANDOM \% 10 * 60)) ; python ./cloudflare-analytics-db.py```. This will sleep for some random minutes before running (\% is escaped due to how cron handle variables).

# Installation
* Install PostgreSQL ```sudo apt install postres``` or run it with [docker].(https://hub.docker.com/_/postgres/)
  * Create the user ```sudo -u postgres createuser -E -P cf_api```
  * Create the database ```sudo -u postgres createdb -O cf_api cf_api```
* Follow the TL;DR above to add it to your crontab. An alternative is to set the ENVIRONMENT directly instead of using the .env file, but I use [autoenv](https://github.com/kennethreitz/autoenv), so it's very convenient for me.

# Why?
* I love Cloudflare and Grafana and wanted to integrate their data in my dashboard, but I needed it to be stored somewhere first :/
* Postgres? I like it, and also, it handles JSON splendidly!

# Todo
- [ ] Add the Grafana dashboard code here as example.
- [ ] Screenshots, because why not!

# Grafana
## Postgres read permissions
```
CREATE USER grafanaread WITH ENCRYPTED PASSWORD '<grafana read-only pw>';
GRANT USAGE ON SCHEMA public to grafanaread;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO grafanareader;
GRANT SELECT ON cf_api TO grafanareader;
```