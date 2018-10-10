# Todo #

* benchmark MariaDB, check if it can sustain 64-128 concurrent connections, especially table INSERTs.
* hook up logging functionality in TUSEMCS to database.
* check growth of database over lifetime of project, assuming realistic candidate rates.
* check lookup performance for various database sizes.
* how should we partition the data for fast lookup?
* check database triggers for retiring old data.
* test performance of various ORMs.
* how useful are these ORMs in practice?
* is it more performant to write raw SQL queries?
