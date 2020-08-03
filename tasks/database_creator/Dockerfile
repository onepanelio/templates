FROM golang:1.14.6 AS builder

WORKDIR /go/src
COPY . .

RUN go build main.go

FROM golang:1.14.6
WORKDIR /go/bin
COPY --from=builder /go/src/main .

CMD ["/go/bin/main"]
