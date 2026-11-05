FROM esperotech/yaade:latest@sha256:24d2d692d948bb09c69d55171cdd9d1bfd9dff041d485fb170430365903226b9

RUN --mount=type=bind,source=patch-frontend.py,target=/tmp/patch-frontend.py \
    cd /app/resources/webroot && python /tmp/patch-frontend.py
