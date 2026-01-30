
#rss_generator.py
import datetime
import io
import os
from xml.sax.saxutils import XMLGenerator
import xml.dom.minidom
from rfeed import *


MAX_ITEMS = 800


class CustomFeed(Feed):
    def __init__(self, title, link, description, language=None, copyright=None, managing_editor=None, web_master=None,
                 pub_date=None, last_build_date=None, categories=None, generator=None, docs=None, cloud=None, ttl=None,
                 image=None, rating=None, text_input=None, skip_hours=None, skip_days=None, items=None,
                 extensions=None):
        super().__init__(title, link, description, language, copyright, managing_editor, web_master, pub_date,
                         last_build_date, categories, generator, docs, cloud, ttl, image, rating, text_input,
                         skip_hours, skip_days, items, extensions)
        self.generator = generator
        self.docs = docs

    def _get_attributes(self):
        attributes = {"version": "2.0"}
        for extension in self.extensions:
            if isinstance(extension, Extension):
                namespace = extension.get_namespace()
                if namespace is not None:
                    attributes = dict(itertools.chain(attributes.items(), namespace.items()))
        return attributes

    def rss(self):
        output = io.BytesIO()
        handler = XMLGenerator(output, 'UTF-8')
        handler.startDocument()

        handler.startElement("rss", self._get_attributes())
        self.publish(handler)
        handler.endElement("rss")
        handler.endDocument()

        parsed = xml.dom.minidom.parse(io.BytesIO(output.getvalue()))
        return parsed.toprettyxml(encoding="UTF-8")


def create_description(rising, row):
    if rising:
        return "Query name: {} | Rank: {} | Search URL: <a href='{}'>{}</a> |" \
               " Increase in Search Frequency %: {} | Breakout: {} | Input Query: {}"\
            .format(row[3], row[1], row[7], row[7], row[9], row[11], row[15])
    return "Query name: {} | Rank: {} | Search URL: <a href='{}'>{}</a> | Popularity %: {}" \
           " | Input Query: {}".format(row[3], row[1], row[7], row[7], row[9], row[13])


def generate_rss(worksheet, rss_filename, buffer, max_col, small_form=False):
    items = []
    rising = 'rising' in rss_filename
    date_index = 13 if rising else 11

    for row in worksheet.iter_rows(min_row=3, max_col=max_col, max_row=worksheet.max_row,
                                   values_only=True):
        if small_form:
            items.append(Item(title=row[3], link=row[5]))
        else:
            items.append(Item(
                title=row[3],
                link=row[5],
                pubDate=datetime.datetime.strptime(row[date_index], '%I:%M:%S %p %d-%m-%Y'),
                description=create_description(rising, row)
            ))

    items = items[-MAX_ITEMS:]

    feed = CustomFeed(
        title=rss_filename,
        link=rss_filename,
        description=rss_filename,
        items=items
    )

    buffer.write(feed.rss())
