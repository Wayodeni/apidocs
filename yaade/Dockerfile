FROM esperotech/yaade:latest@sha256:24d2d692d948bb09c69d55171cdd9d1bfd9dff041d485fb170430365903226b9

RUN --mount=type=bind,source=PatchResponseDownload.java,target=/tmp/PatchResponseDownload.java \
    javac --add-exports java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED \
        -cp '/app/libs/*' -d /tmp/response-download /tmp/PatchResponseDownload.java \
    && java --add-exports java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED \
        -cp /tmp/response-download com.espero.yaade.services.PatchResponseDownload /app/classes \
    && cp /tmp/response-download/com/espero/yaade/services/ResponseDownload.class \
        /app/classes/com/espero/yaade/services/ \
    && rm -r /tmp/response-download

RUN --mount=type=bind,source=patch-frontend.py,target=/tmp/patch-frontend.py \
    cd /app/resources/webroot && python /tmp/patch-frontend.py
