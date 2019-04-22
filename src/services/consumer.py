import os
import sys
from db_service import DbService
from messaging_service import MessagingService
from image_service import ImageService
from fetch_service import FetchService

db_service = DbService()
image_service = ImageService()
fetch_service = FetchService()

dimensions = (320, 320,)

def build_names_and_paths(record):
    file_name = record['url'].split('/')[-1]
    download_path = '/tmp/{}'.format(file_name)
    thumbnail_path = '/waldo-app-thumbs/{}.jpeg'.format(record['uuid'])
    return (file_name, download_path, thumbnail_path)

def process_record(record):
    file_name, download_path, thumbnail_path = build_names_and_paths(record)
    db_service.set_status(record['uuid'], 'processing')
    fetch_service.download(record['url'], download_path)
    image_service.resize(dimensions, download_path, thumbnail_path)
    db_service.add_thumbnail(record['uuid'], dimensions[0], dimensions[1], thumbnail_path)
    db_service.set_status(record['uuid'], 'completed')

def callback(_id):
    id = str(_id)
    record = None

    try:
        record = db_service.get_by_id(id)
        if record is None:
            print('[consumer] Record with id \"{}\" does not exist.'.format(id))
    except Exception as ex:
        print('[consumer] Could not fetch id \"{}\": {}'.format(id, ex))
        record = None

    if record is not None:
        try:
            process_record(record)
            print('[consumer] Processed \"{}\"'.format(id))
        except Exception as ex:
            print('[consumer] Could not process id \"{}\": {}'.format(id, ex))
            db_service.set_status(id, 'failed')

    return True

def app():
    try:
        print('[consumer] Starting app!')
        MessagingService().consume(callback)
        print('[consumer] Consumer has exited!')
    except Exception as ex:
        print('[consumer] FAILED starting app: {}'.format(ex))
        return

if __name__ == '__main__':
    app()
