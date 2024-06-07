package main

import (
	"database/sql"
	"fmt"
	"log"
	"math/rand"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

func init() {

	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	createTableSQL := `CREATE TABLE IF NOT EXISTS example (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			data TEXT
		);`
	_, err = db.Exec(createTableSQL)
	if err != nil {
		log.Fatal(err)
	}

	insertSQL := `INSERT INTO example (data) VALUES (?)`
	stmt, err := db.Prepare(insertSQL)
	if err != nil {
		log.Fatal(err)
	}
	defer stmt.Close()

	rand.Seed(time.Now().UnixNano())
	for i := 0; i < 10; i++ {
		randomData := fmt.Sprintf("random_data_%d", rand.Intn(100))
		_, err = stmt.Exec(randomData)
		if err != nil {
			log.Fatal(err)
		}
	}

	rows, err := db.Query("SELECT id, data FROM example")
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	for rows.Next() {
		var id int
		var data string
		err = rows.Scan(&id, &data)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Printf("ID: %d, Data: %s\n", id, data)
	}
	err = rows.Err()
	if err != nil {
		log.Fatal(err)
	}
}
