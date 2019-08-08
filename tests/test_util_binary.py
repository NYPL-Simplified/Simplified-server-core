# Test the binary helper classes in util.binary.

from nose.tools import eq_
import base64 as stdlib_base64
from ..util.binary import (
    UnicodeAwareBase64,
    base64
)

class TestUnicodeAwareBase64(object):

    def test_encoding(self):        
        string = "םולש"

        # Test with two different underlying encodings that can handle
        # Hebrew characters.
        self._test_encoder(string, UnicodeAwareBase64("utf8"))
        self._test_encoder(string, UnicodeAwareBase64("iso-8859-8"))

    def _test_encoder(self, string, base64):
        # Create a binary version of the string in the encoder's
        # encoding, for use in comparisons.
        binary = string.encode(base64.encoding)

        # Test all supported methods of the base64 API.
        for encode, decode in [
            ('b64encode', 'b64decode'),
            ('standard_b64encode', 'standard_b64decode'),
            ('urlsafe_b64encode', 'urlsafe_b64decode'),
            ('encodestring', 'decodestring')
        ]:
            encode_method = getattr(base64, encode)
            decode_method = getattr(base64, decode)

            # Test a round-trip. Base64-encoding a Unicode string and
            # then decoding it should give the original string.
            encoded = encode_method(string)
            decoded = decode_method(encoded)
            eq_(string, decoded)

            # Test encoding on its own. Encoding with a
            # UnicodeAwareBase64 and then converting to ASCII should
            # give the same result as running the binary
            # representation of the string through the default bas64
            # module.
            base_encode = getattr(stdlib_base64, encode)
            base_encoded = base_encode(binary)
            eq_(base_encoded, encoded.encode("ascii"))

            # If you pass in a bytes object to a UnicodeAwareBase64
            # method, it's no problem. You get a Unicode string back.
            eq_(encoded, encode_method(binary))
            eq_(decoded, decode_method(base_encoded))

    def test_default_is_base64(self):
        # If you import "base64" from util.binary, you get a
        # UnicodeAwareBase64 object that encodes as UTF-8 by default.
        assert isinstance(base64, UnicodeAwareBase64)
        eq_("utf8", base64.encoding)
        snowman = "☃"
        snowman_utf8 = snowman.encode("utf8")
        as_base64 = base64.b64encode(snowman)
        eq_("4piD", as_base64)

        # This is a Unicode representation of the string you'd get if
        # you encoded the snowman as UTF-8, then used the standard
        # library to base64-encode the bytestring.
        eq_(b"4piD", stdlib_base64.b64encode(snowman_utf8))
