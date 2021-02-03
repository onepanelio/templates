FROM golang:1.15 AS builder

WORKDIR /go/src
COPY . .
RUN go build -o /go/bin/filesyncer

FROM python:3.7-slim

ENV PATH="/go/bin:${PATH}"
COPY --from=builder /go/bin/filesyncer /go/bin/
RUN pip install awscli==1.15.58
ENTRYPOINT ["filesyncer"]