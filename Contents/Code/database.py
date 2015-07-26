import sqlite3

TABLE_CREATION = [
    """
    PRAGMA journal_mode=WAL
    """,
    """
    CREATE TABLE IF NOT EXISTS Bouquet(
      service_reference  CHAR PRIMARY KEY NOT NULL ,
      service_name  CHAR
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Event(
      event_id INTEGER NOT NULL ,
      event_start INTEGER ,
      event_duration INTEGER ,
      event_title CHAR ,
      event_description CHAR ,
      event_description_extended CHAR,
      ch_id CHAR NOT NULL,
      PRIMARY KEY(event_id, ch_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS Channel(
      service_reference  CHAR PRIMARY KEY NOT NULL,
      service_name  CHAR,
      bo_id CHAR
    )
    """,
    """
    CREATE VIEW IF NOT EXISTS NowNext AS
    select service_name, event_id, event_title, event_description, event_description_extended, ch_id, remaining from
      Channel
    INNER JOIN (

        SELECT event_id, event_title, event_description, event_description_extended, ch_id, event_start,
          ((CAST(event_start AS INTEGER) + CAST(event_duration AS INTEGER)) - CAST(strftime('%s', 'now') AS INTEGER)) / 60 AS remaining
        FROM Event
        WHERE  (CAST(event_start AS INTEGER) < CAST(strftime('%s', 'now') AS INTEGER)
        AND (CAST(event_start AS INTEGER) + CAST(event_duration AS INTEGER)) > CAST(strftime('%s', 'now') AS INTEGER) /* Now*/)
        UNION


        SELECT event_id, event_title, event_description, event_description_extended, ch_id, event_start, NULL FROM   Event e
        WHERE e.event_start = (
        SELECT MIN(ev.event_start)
        FROM Event ev WHERE ev.ch_id = e.ch_id
        AND (CAST(event_start AS INTEGER) > CAST(strftime('%s', 'now') AS INTEGER) )
        )

    ) a
    ON a.ch_id = Channel.service_reference
    """,
    """
    CREATE  INDEX IF NOT EXISTS "main"."idx_event_event_times" ON "Event" ("event_start" ASC, "event_duration" ASC)
    """

]


class DB():

    def __init__(self):
        try:
            self.myDB = sqlite3.connect('receiver.sqlite', timeout=30, check_same_thread=False)
            self.myDB.row_factory = sqlite3.Row
            self.cu = self.myDB.cursor()

            for table in TABLE_CREATION:
                self.cu.execute(table)
                self.myDB.commit()

        except:
            raise

    def insert(self, table, data):



        cols = ','.join(data[0].keys())
        vals = ', '.join('?' * len(data[0].keys()))

        data = [tuple(data.values()) for data in data]



        sql = """INSERT INTO {} ({}) values({})""".format(table, cols, vals)

        cu = self.myDB.cursor()
        for d in data:

            try:
                cu.execute(sql, d )

            except sqlite3.IntegrityError:
                print d
                pass
        self.myDB.commit()

    def get (self, table, column_list=None, where=None):


        cols = ','.join(column_list) if column_list else '*'

        sql = """SELECT {} FROM {} """.format(cols, table)
        if where:
            where = """ WHERE {} = '{}' """.format(where.keys()[0], where.values()[0])
            sql = sql + where
        rows = self.cu.execute(sql)

        return rows

    def raw_sql(self, sql):

        return self.cu.execute(sql)






db = DB()