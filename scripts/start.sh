#! /usr/bin/env sh

./scripts/wait-for.sh postgres:5432 -- echo "postgres is up"
./scripts/wait-for.sh rabbitmq:5672 -- echo "rabbitmq is up"

/usr/bin/supervisord -c /etc/supervisord.conf
# python src/services/consumer.py &
# python src/services/web.py
