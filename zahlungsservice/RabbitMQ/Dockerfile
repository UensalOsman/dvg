FROM rabbitmq:3-management

ENV RABBITMQ_DEFAULT_USER=
ENV RABBITMQ_DEFAULT_PASS=

COPY RabbitMQ.conf /etc/rabbitmq/conf.d/30-custom.conf
COPY definitions.json /etc/rabbitmq/definitions.json

# Management-Plugin aktivieren (UI auf Port 15672)
RUN rabbitmq-plugins enable --offline rabbitmq_management
