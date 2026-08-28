import csv, codecs, io


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def __next__(self):
        return self.reader.next().encode("utf-8")


class UnicodeCSVReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, encoding="utf-8", delimiter=';',
                 quotechar='"', **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, delimiter=delimiter,
                                 quotechar=quotechar, **kwds)

    def __next__(self):
        row = next(self.reader)
        return [str(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeCSVDictReader:
    def __init__(self, f, encoding='utf-8', delimiter=';',
                 quotechar='"', **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.DictReader(f, delimiter=delimiter,
                                     quotechar=quotechar, **kwds)

    def __next__(self):
        row = next(self.reader)
        return dict([(str(key, 'utf-8'), str(value, 'utf-8')) \
                         for key, value in row.items()])

    def __iter__(self):
        return self


class UnicodeCSVWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = io.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
