FROM golang:1.24-alpine AS build

RUN CGO_ENABLED=0 go install github.com/minio/minio@latest \
    && CGO_ENABLED=0 go install github.com/minio/mc@latest

FROM alpine:3.21

COPY --from=build /go/bin/minio /usr/local/bin/minio
COPY --from=build /go/bin/mc /usr/local/bin/mc

ENTRYPOINT ["minio"]
