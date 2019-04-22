# photo-processor

## Intro

My day-to-day duties do not avail me of a lot of Python; once, I was a much more
regular user. That being said, I love to learn and this has been a really fun
crash course/refresher!

## Setup/Run

Simply `make start`; run `make db-schema` after boot-up to ensure all data is
present. The container uses [supervisor](http://supervisord.org/) to orchestrate
and keep alive the consumer and web processes.

From the root, you can run `make test` to run the (admittedly incomplete) suite
of unit tests - no backends required.

## Usage
Hitting the `pending` status endpoint is straightforward:

```bash
$ curl http://localhost:3000/photos/pending
```

At first, I had genericized the method to accept any status, and feed it to the
database service:

```python
@app.route('/photos/<status>')
def get_photos_by_status(status):
    try:
        results = db_service.get_by_status(status)
    ...
```

I then figured, "Don't overdo it, you weren't asked for that!" Instead I will
memorialize that implementation here!

The new API endpoint at `/photos/process` expects a JSON array with one or more
UUIDs:

```bash
$ curl -d '[ "efca73b0-0697-4325-af90-d272f01b1ae5" ]' http://localhost:3000/photos/process | jq .
{
  "accepted": [
    "efca73b0-0697-4325-af90-d272f01b1ae5"
  ],
  "rejected": []
}

$ curl -d '[ "efca73b0-0697-4325-af90-d272f01b1ae5", "42806f82-b389-4f0d-9c94-f4145377e617" ]' http://localhost:3000/photos/process | jq .
{
  "accepted": [
    "efca73b0-0697-4325-af90-d272f01b1ae5",
    "42806f82-b389-4f0d-9c94-f4145377e617"
  ],
  "rejected": []
}
```

The API will accept the parts of a request that it can accommodate:

```bash
$ curl -d '[ "efca73b0-0697-4325-af90-d272f01b1ae5", "13f4ac37-1eeb-4a21-8a2a-b9763d6093e0", "foobar" ]' http://localhost:3000/photos/process | jq .

{
  "accepted": [
    "efca73b0-0697-4325-af90-d272f01b1ae5",
    "13f4ac37-1eeb-4a21-8a2a-b9763d6093e0"
  ],
  "rejected": [
    "foobar"
  ]
}
```

Note that "accepted" simply means that the UUID has been queued, and does not
indicate anything about consumer processing. "rejected" means the web layer
completely rejected that data. If all of the packets are rejected:

```bash
$ curl -v -d '[ "foo", "bar", "baz" ]' http://localhost:3000/photos/process
*   Trying ::1...
* TCP_NODELAY set
* Connected to localhost (::1) port 3000 (#0)
> POST /photos/process HTTP/1.1
> Host: localhost:3000
> User-Agent: curl/7.54.0
> Accept: */*
> Content-Length: 23
> Content-Type: application/x-www-form-urlencoded
>
* upload completely sent off: 23 out of 23 bytes
* HTTP 1.0, assume close after body
< HTTP/1.0 400 BAD REQUEST
< Content-Type: application/json
< Content-Length: 68
< Server: Werkzeug/0.15.2 Python/3.7.2
< Date: Mon, 22 Apr 2019 10:32:52 GMT
<
{"message":"None of the provided inputs could be parsed as a UUID"}
* Closing connection 0
```

An empty payload will yield a vacuously accepted response:

```bash
$ curl -v -d '[]' http://localhost:3000/photos/process
*   Trying ::1...
* TCP_NODELAY set
* Connected to localhost (::1) port 3000 (#0)
> POST /photos/process HTTP/1.1
> Host: localhost:3000
> User-Agent: curl/7.54.0
> Accept: */*
> Content-Length: 2
> Content-Type: application/x-www-form-urlencoded
>
* upload completely sent off: 2 out of 2 bytes
* HTTP 1.0, assume close after body
< HTTP/1.0 201 CREATED
< Content-Type: application/json
< Content-Length: 30
< Server: Werkzeug/0.15.2 Python/3.7.2
< Date: Mon, 22 Apr 2019 10:34:51 GMT
<
{"accepted":[],"rejected":[]}
* Closing connection 0
```

The consumer will be quietly running in the background, throwing images into the
mapped volume and updating statuses on the photos themselves.

## Trivia and Thoughts

* I was not sure about joining to `photo_thumbnails` at any point. The object
generation would be a simple binning exercise though (however untested):

```python
def create_object_from_row(self, uuid, url, status, created_at):
    return {
        'uuid': uuid,
        'url': url,
        'status': status,
        'created_at': created_at,
        'thumbnails': []
    }

def create_thumbnail(self, uuid, width, height, created_at):
    return {
        'uuid': uuid,
        'width': width,
        'height': height,
        'created_at': created_at
    }

def fetch_by(self, col, val):
    columns = ('p.uuid', 'p.url', 'p.status', 'p.created_at', 't.uuid', 't.photo_uuid', 't.width', 't.height', 't.created_at')
    query = 'SELECT {} FROM photos AS p INNER JOIN photo_thumbnails AS t ON p.uuid = t.photo_uuid WHERE {} = %s'.format(', '.join(columns), col)
    rows = self.execute_sql_with_response(query, val)
    cache = {}
    for row in rows:
        new_thumbnail = self.create_thumbnail(row[4], row[6], row[7], row[8])
        if not row[0] in cache:
            cache[row[0]] = self.create_object_from_row(row[0], row[1], row[2], row[3])
        cache[row[0]]['thumbnails'].append(new_thumbnail)
    return list(cache.values())
```

* I figured, given the scope and scale of this project, that introducing
[SQLAlchemy](https://www.sqlalchemy.org/) might be a little too heavyweight.
That being said, all this nasty, brittle rehydration logic would look much
nicer as a consequence; the join to `photo_thumbnails` would be a mucher cleaner
operation as well.

* The `photo_thumbnails__photo_uuid__width__height_uniq` index was added when
I realized how heavily saturated the database would be as a consequence of
hitting this endpoint repeatedly. Instead, realizing there would be commonality
between the image name, width, and height, I added the constraint so that the
insert would simply stop (`ON CONFLICT...DO NOTHING`).

* The tests are rough around the edges, to be sure. To be honest, I have not
worked with Python's `unittest` facilities before, and I thought it would be fun
to give it a try. That being said, there is something off about my project still,
such that running the tests agnostically of the root directory isn't all that
great. I would loved to have thrown code coverage in there as well, but in the
interest of time I demurred.

* I think async would have behooved this project a bunch: considering how
task-oriented it was, an asynchronous web framework is not only germane to the
spirit of this project, but would have made integrating asyncio libraries
(particularly RabbitMQ) a breeze. That being said, the reality is there is
usually more code to maintain than to re-innovate, and I decided to keep it
as-is.
