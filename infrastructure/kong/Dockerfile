FROM kong:3.6
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 curl && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /kong/declarative && chown -R kong:kong /kong/declarative
COPY kong.template.yml /kong/kong.template.yml
COPY init-kong.sh /kong/init-kong.sh
RUN chmod +x /kong/init-kong.sh
USER kong
ENTRYPOINT ["/kong/init-kong.sh"]
