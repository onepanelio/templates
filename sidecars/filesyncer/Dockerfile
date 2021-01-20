FROM golang:1.15 AS builder

WORKDIR /go/src
COPY . .
RUN go build -o /go/bin/filesyncer

FROM amazon/aws-cli:2.1.20

ENV PATH="/go/bin:${PATH}"
COPY --from=builder /go/bin/filesyncer /go/bin/
ENTRYPOINT ["filesyncer"]