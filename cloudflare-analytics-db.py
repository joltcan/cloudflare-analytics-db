#!/usr/bin/env python

import psycopg2
import requests
import json
import os,sys

cf_api_url = "https://api.cloudflare.com/client/v4/zones"

db_url = os.getenv('DATABASE_URL')
if db_url:
    db = psycopg2.connect(os.getenv('DATABASE_URL'))
else:
    print("No secret parameters was found. Did you create .env or set environment variables?")
    sys.exit(1)

try:
    with db.cursor() as cursor:
        # Initiate tables if they don't exist
        sql = "select * from pg_catalog.pg_tables where tablename='cf_api'"
        cursor.execute(sql)
        result = cursor.fetchone()

        if not result:
            try:
                sql = """CREATE TABLE cf_api (
                    id serial primary key,
                    data jsonb
                    )"""
                cursor.execute(sql)
                db.commit()
                print "Created initial tables"
            except Exception as e:
                print "Cant initialize db: %s" % e
                sys.exit(666)


        # Query PSQL for the last 24 existing dates
        sql = "select data->>'until' as ts from cf_api order by ts desc limit 24"
        cursor.execute(sql)
        result = cursor.fetchall()

        # make a nice list for later
        existing_dates = []
        if result:
            for entry in result:
                existing_dates.append(entry[0])

        # setup some headers
        cf_headers = {"X-Auth-Email" : os.getenv('CLOUDFLARE_EMAIL'),
                    "X-Auth-Key" : os.getenv('CLOUDFLARE_API_KEY'),
                    "Content-Type" : "application/json"}

        # Query CF for the site id
        r = requests.get(cf_api_url + '?name=' + os.getenv('CLOUDFLARE_ZONE'), headers=cf_headers)
        cf = r.json()

        # hardcode first result, since it should only be one match with that domain:
        cf_site_id = cf['result'][0]['id']

        # Query CF again, but get the analytics data with the site id.
        # This gives us the last 24h with 1h resolution (found by trial and error)
        # Reference: https://api.cloudflare.com/#zone-analytics-dashboard
        # Free accounts have limits on the resolution that can be requested (-1440 works).
        
        # if we don't have any existing dates, grab as many as we can.
        if not existing_dates:
            cf_params = {'since': '-4319'}
        else:
            cf_params = {'since': '-1440'}

        r = requests.get(cf_api_url + '/' + cf_site_id + '/analytics/dashboard', headers=cf_headers,params=cf_params)
        cf_data = r.json()
        if cf_data['success']:
            entrycounter = 0
            for entry in cf_data['result']['timeseries']:
                if entry['until'] not in existing_dates:
                    entrycounter += 1

                    # I don't use it, override if you still want 'em            
                    if not os.getenv('CLOUDFLARE_COUNTRIES'):
                        del entry['threats']['country']
                        del entry['bandwidth']['country']
                        del entry['requests']['country']

                    # lets put them in the db
                    sql = "insert into cf_api (data) VALUES ('%s')" % json.dumps(entry)
                    cursor.execute(sql)

            # Did we have any entries? Then commit!
            if entrycounter > 0:
                db.commit()
        
        # If the query isn't a success, print the response
        else:
            print json.dumps(cf_data, indent=4)

finally:
    db.close()