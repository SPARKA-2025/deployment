FROM base-sparka-api-image:latest

WORKDIR /app

COPY . .

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5001

CMD ["/usr/bin/supervisord"]
