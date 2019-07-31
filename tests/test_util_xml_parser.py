# encoding: utf-8
from nose.tools import (
    assert_raises,
    eq_,
    set_trace,
)

from ..util.xmlparser import XMLParser
from lxml.etree import XMLSyntaxError

class MockParser(XMLParser):
    """A mock XMLParser that just returns every tag it hears about."""

    def process_one(self, tag, namespaces):
        return tag

class TestXMLParser(object):

    def test_process_all(self):
        # Verify that process_all can handle either XML markup
        # or an already-parsed tag object.
        data = '<atag>This is a tag.</atag>'

        # Try it with markup.
        parser = MockParser()
        [tag] = parser.process_all(data, "/*")
        eq_("atag", tag.tag)
        eq_("This is a tag.", tag.text)

        # Try it with a tag.
        [tag2] = parser.process_all(tag, "/*")
        eq_(tag, tag2)

    def test_process_all_with_xpath(self):
        # Verify that process_all processes only tags that
        # match the given XPath expression.
        data = '<parent><a>First</a><b>Second</b><a>Third</a></parent><a>Fourth</a>'

        parser = MockParser()

        # Only process the <a> tags beneath the <parent> tag.
        [tag1, tag3] = parser.process_all(data, "/parent/a")
        eq_("First", tag1.text)
        eq_("Third", tag3.text)

    def test_invalid_characters_are_stripped(self):
        data = '<?xml version="1.0" encoding="utf-8"><tag>I enjoy invalid characters, such as \x00\x01 and \x1F. But I also like \xe2\x80\x9csmart quotes\xe2\x80\x9d.</tag>'
        parser = MockParser()
        [tag] = parser.process_all(data, "/tag")
        eq_('I enjoy invalid characters, such as  and . But I also like “smart quotes”.', tag.text)

    def test_invalid_entities_are_stripped(self):
        data = '<?xml version="1.0" encoding="utf-8"><tag>I enjoy invalid entities, such as &#x00;&#x01; and &#x1F;</tag>'
        parser = MockParser()
        [tag] = parser.process_all(data, "/tag")
        eq_('I enjoy invalid entities, such as  and ', tag.text)
