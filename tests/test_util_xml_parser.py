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

    def test_invalid_characters_are_stripped(self):
        data = u"<tag>I enjoy invalid characters, such as \x00 and \x1F</tag>"
        parser = MockParser()
        [tag] = parser.process_all(data, "/tag")
        eq_('I enjoy invalid characters, such as  and ', tag.text)

    def test_exception_when_scrub_fails(self):
        # Reraise the lxml exception if invalid characters somehow
        # make it through the scrubbing process.
        class Mock(MockParser):
            def scrub_xml(cls, xml):
                # Don't scrub at all.
                return xml

        data = u"<tag>I enjoy invalid characters, such as \x00 and \x1F</tag>"
        parser = Mock()
        assert_raises(XMLSyntaxError, list, parser.process_all(data, "/tag"))