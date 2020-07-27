package main

import (
	"database/sql"
	"fmt"
	_ "github.com/lib/pq"
	"log"
	"os"
	"strconv"
)

// DatabaseConnection holds the information required to connect to a database
type DatabaseConnection struct {
	Host string
	Password string
	Username string
	Port int
	DriverName string
	DefaultDatabaseName string
}

func (d *DatabaseConnection) DataSourceName() string {
	return fmt.Sprintf("host=%v user=%v password=%v dbname=%v sslmode=disable",
		d.Host, d.Username, d.Password, d.DefaultDatabaseName)
}

// GetDatabaseConnectionFromEnvironment loads DatabaseConnection information from environment variables
func GetDatabaseConnectionFromEnvironment() (*DatabaseConnection, error) {
	conn := &DatabaseConnection{
		Host:       os.Getenv("HOST"),
		Password:   os.Getenv("PASSWORD"),
		Username:   os.Getenv("USERNAME"),
		DriverName: os.Getenv("DRIVER_NAME"),
		DefaultDatabaseName: os.Getenv("DEFAULT_DATABASE_NAME"),
	}

	if conn.DefaultDatabaseName == "" {
		conn.DefaultDatabaseName = conn.Username
	}

	port, err := strconv.Atoi(os.Getenv("PORT"))
	if err != nil {
		return nil, err
	}

	conn.Port = port

	return conn, nil
}

// createDatabase connects to the database and create a new database given the input name
func createDatabase(conn *DatabaseConnection, newDatabaseName string) error {
	db, err := sql.Open(conn.DriverName, conn.DataSourceName())
	if err != nil {
		return err
	}
	defer db.Close()

	_, err = db.Exec("CREATE DATABASE "+ newDatabaseName)

	return err
}

// main loads the database connection information from environment variables, and attempts to create a new database.
func main()  {
	dbConnInfo, err := GetDatabaseConnectionFromEnvironment()
	if err != nil {
		log.Printf("[error] Unable to get database connection info from env vars.\nErr:%v", err)
		return
	}

	newDatabaseName := os.Getenv("NEW_DATABASE_NAME")
	if newDatabaseName == "" {
		log.Printf("[error] Unable to get NEW_DATABASE_NAME environment variable, or it is empty")
		return
	}

	if err := createDatabase(dbConnInfo, newDatabaseName); err != nil {
		log.Printf("[error] creating database: %v", err)
		return
	}

	log.Printf("Successfully created database \"%v\"", newDatabaseName)
}