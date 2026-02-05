FROM quay.io/keycloak/keycloak:24.0
COPY realm-export.json /opt/keycloak/data/import/realm-export.json
COPY import-realm.sh /opt/keycloak/import-realm.sh
ENTRYPOINT ["/opt/keycloak/import-realm.sh"]
