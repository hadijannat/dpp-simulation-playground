FROM kong:3.6
USER root
RUN apk add --no-cache python3 curl
COPY kong.template.yml /kong/kong.template.yml
COPY init-kong.sh /kong/init-kong.sh
RUN chmod +x /kong/init-kong.sh
USER kong
ENTRYPOINT ["/kong/init-kong.sh"]
