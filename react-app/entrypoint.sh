#!/bin/sh

JS_DIR="/usr/share/nginx/html/static/js"

API_URL_STRING="https://vnuqp5djfa.execute-api.eu-west-1.amazonaws.com/prod"
USER_POOL_ID_STRING="eu-west-1_6pfNYzm8q"
APP_CLIENT_ID_STRING="7bldv2hshvji3vnctr6gs8rjd6"

API_URL_REPLACEMENT=${API_URL_REPLACEMENT:-$API_URL_STRING}
USER_POOL_ID_REPLACEMENT=${USER_POOL_ID_REPLACEMENT:-$USER_POOL_ID_STRING}
APP_CLIENT_ID_REPLACEMENT=${APP_CLIENT_ID_REPLACEMENT:-$APP_CLIENT_ID_STRING}

for file in $JS_DIR/*.js; do
    echo "Replacing URL in $file..."

    sed -i "s|$API_URL_STRING|$API_URL_REPLACEMENT|g" "$file"
    sed -i "s|$USER_POOL_ID_STRING|$USER_POOL_ID_REPLACEMENT|g" "$file"
    sed -i "s|$APP_CLIENT_ID_STRING|$APP_CLIENT_ID_REPLACEMENT|g" "$file"
done

echo "Starting Nginx..."
exec "$@"
