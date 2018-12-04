from nose.tools import (
    eq_,
    set_trace,
    assert_raises,
)
import datetime
from pymarc import Record, MARCReader
from StringIO import StringIO
import urllib

from . import DatabaseTest

from ..model import (
    CachedMARCFile,
    Contributor,
    DataSource,
    DeliveryMechanism,
    Edition,
    ExternalIntegration,
    Genre,
    Identifier,
    LicensePoolDeliveryMechanism,
    MaterializedWorkWithGenre,
    Representation,
    RightsStatus,
)
from ..config import CannotLoadConfiguration

from ..marc import (
  Annotator,
  MARCExporter,
)

from ..s3 import (
    MockS3Uploader,
    S3Uploader,
)
from ..lane import WorkList

class TestAnnotator(DatabaseTest):

    def test_annotate_work_record(self):
        # Verify that annotate_work_record adds the distributor and formats.
        class MockAnnotator(Annotator):
            add_distributor_called_with = None
            add_formats_called_with = None
            def add_distributor(self, record, pool):
                self.add_distributor_called_with = [record, pool]
            def add_formats(self, record, pool):
                self.add_formats_called_with = [record, pool]

        annotator = MockAnnotator()
        record = Record()
        work = self._work(with_license_pool=True)
        pool = work.license_pools[0]
        
        annotator.annotate_work_record(work, pool, None, None, record)
        eq_([record, pool], annotator.add_distributor_called_with)
        eq_([record, pool], annotator.add_formats_called_with)

    def test_leader(self):
        work = self._work(with_license_pool=True)
        leader = Annotator.leader(work)
        eq_("00000nam  2200000   4500", leader)

        # If there's already a marc record cached, the record status changes.
        work.marc_record = "cached"
        leader = Annotator.leader(work)
        eq_("00000cam  2200000   4500", leader)

    def _check_control_field(self, record, tag, expected):
        [field] = record.get_fields(tag)
        eq_(expected, field.value())

    def _check_field(self, record, tag, expected_subfields, expected_indicators=None):
        if not expected_indicators:
            expected_indicators = [" ", " "]
        [field] = record.get_fields(tag)
        eq_(expected_indicators, field.indicators)
        for subfield, value in expected_subfields.items():
            eq_(value, field.get_subfields(subfield)[0])

    def test_add_control_fields(self):
        # This edition has one format and was published before 1900.
        edition, pool = self._edition(with_license_pool=True)
        identifier = pool.identifier
        edition.issued = datetime.datetime(956, 1, 1)

        now = datetime.datetime.now()
        record = Record()
        
        Annotator.add_control_fields(record, identifier, pool, edition)
        self._check_control_field(record, "001", identifier.urn)
        assert now.strftime("%Y%m%d") in record.get_fields("005")[0].value()
        self._check_control_field(record, "006", "m        d        ")
        self._check_control_field(record, "007", "cr cn ---anuuu")
        self._check_control_field(
            record, "008",
            now.strftime("%y%m%d") + "s0956    xxu                 eng  ")

        # This French edition has two formats and was published in 2018.
        edition2, pool2 = self._edition(with_license_pool=True)
        identifier2 = pool2.identifier
        edition2.issued = datetime.datetime(2018, 2, 3)
        edition2.language = "fre"
        LicensePoolDeliveryMechanism.set(
            pool2.data_source, identifier2, Representation.PDF_MEDIA_TYPE,
            DeliveryMechanism.ADOBE_DRM, RightsStatus.IN_COPYRIGHT)

        record = Record()
        Annotator.add_control_fields(record, identifier2, pool2, edition2)
        self._check_control_field(record, "001", identifier2.urn)
        assert now.strftime("%Y%m%d") in record.get_fields("005")[0].value()
        self._check_control_field(record, "006", "m        d        ")
        self._check_control_field(record, "007", "cr cn ---mnuuu")
        self._check_control_field(
            record, "008",
            now.strftime("%y%m%d") + "s2018    xxu                 fre  ")

    def test_add_marc_organization_code(self):
        record = Record()
        Annotator.add_marc_organization_code(record, "US-MaBoDPL")
        self._check_control_field(record, "003", "US-MaBoDPL")

    def test_add_isbn(self):
        isbn = self._identifier(identifier_type=Identifier.ISBN)
        record = Record()
        Annotator.add_isbn(record, isbn)
        self._check_field(record, "020", {"a": isbn.identifier})

        # If the identifier isn't an ISBN, but has an equivalent that is, it still
        # works.
        equivalent = self._identifier()
        data_source = DataSource.lookup(self._db, DataSource.OCLC)
        equivalent.equivalent_to(data_source, isbn, 1)
        record = Record()
        Annotator.add_isbn(record, equivalent)
        self._check_field(record, "020", {"a": isbn.identifier})

        # If there is no ISBN, the field is left out.
        non_isbn = self._identifier()
        record = Record()
        Annotator.add_isbn(record, non_isbn)
        eq_([], record.get_fields("020"))

    def test_add_title(self):
        edition = self._edition()
        edition.title = "The Good Soldier"
        edition.sort_title = "Good Soldier, The"
        edition.subtitle = "A Tale of Passion"

        record = Record()
        Annotator.add_title(record, edition)
        [field] = record.get_fields("245")
        self._check_field(
            record, "245", {
                "a": edition.title,
                "b": edition.subtitle,
                "c": edition.author,
            }, ["0", "4"])

    def test_add_contributors(self):
        author = "a"
        author2 = "b"
        translator = "c"

        # Edition with one author gets a 100 field and no 700 fields.
        edition = self._edition(authors=[author])
        edition.sort_author = "sorted"

        record = Record()
        Annotator.add_contributors(record, edition)
        eq_([], record.get_fields("700"))
        self._check_field(record, "100", {"a": edition.sort_author}, ["1", " "])

        # Edition with two authors and a translator gets three 700 fields and no 100 fields.
        edition = self._edition(authors=[author, author2])
        edition.add_contributor(translator, Contributor.TRANSLATOR_ROLE)

        record = Record()
        Annotator.add_contributors(record, edition)
        eq_([], record.get_fields("100"))
        fields = record.get_fields("700")
        for field in fields:
            eq_(["1", " "], field.indicators)
        [author_field, author2_field, translator_field] = sorted(fields, key=lambda x: x.get_subfields("a")[0])
        eq_(author, author_field.get_subfields("a")[0])
        eq_(Contributor.PRIMARY_AUTHOR_ROLE, author_field.get_subfields("e")[0])
        eq_(author2, author2_field.get_subfields("a")[0])
        eq_(Contributor.AUTHOR_ROLE, author2_field.get_subfields("e")[0])
        eq_(translator, translator_field.get_subfields("a")[0])
        eq_(Contributor.TRANSLATOR_ROLE, translator_field.get_subfields("e")[0])

    def test_add_publisher(self):
        edition = self._edition()
        edition.publisher = self._str
        edition.issued = datetime.datetime(1894, 4, 5)

        record = Record()
        Annotator.add_publisher(record, edition)
        self._check_field(
            record, "264", {
                "a": "[Place of publication not identified]",
                "b": edition.publisher,
                "c": "1894",
            }, [" ", "1"])

        # If there's no publisher, the field is left out.
        record = Record()
        edition.publisher = None
        Annotator.add_publisher(record, edition)
        eq_([], record.get_fields("264"))

    def test_add_distributor(self):
        edition, pool = self._edition(with_license_pool=True)
        record = Record()
        Annotator.add_distributor(record, pool)
        self._check_field(record, "264", {"b": pool.data_source.name}, [" ", "2"])

    def test_add_physical_description(self):
        book = self._edition()
        book.medium = Edition.BOOK_MEDIUM
        audio = self._edition()
        audio.medium = Edition.AUDIO_MEDIUM

        record = Record()
        Annotator.add_physical_description(record, book)
        self._check_field(record, "300", {"a": "1 online resource"})
        self._check_field(record, "336", {
            "a": "text",
            "b": "txt",
            "2": "rdacontent",
        })
        self._check_field(record, "337", {
            "a": "computer",
            "b": "c",
            "2": "rdamedia",
        })
        self._check_field(record, "338", {
            "a": "online resource",
            "b": "cr",
            "2": "rdacarrier",
        })
        self._check_field(record, "347", {
            "a": "text file",
            "2": "rda",
        })
        self._check_field(record, "380", {
            "a": "eBook",
            "2": "tlcgt",
        })

        record = Record()
        Annotator.add_physical_description(record, audio)
        self._check_field(record, "300", {
            "a": "1 sound file",
            "b": "digital",
        })
        self._check_field(record, "336", {
            "a": "spoken word",
            "b": "spw",
            "2": "rdacontent",
        })
        self._check_field(record, "337", {
            "a": "computer",
            "b": "c",
            "2": "rdamedia",
        })
        self._check_field(record, "338", {
            "a": "online resource",
            "b": "cr",
            "2": "rdacarrier",
        })
        self._check_field(record, "347", {
            "a": "audio file",
            "2": "rda",
        })
        eq_([], record.get_fields("380"))

    def test_add_audience(self):
        for audience, term in Annotator.AUDIENCE_TERMS.items():
            work = self._work(audience=audience)
            record = Record()
            Annotator.add_audience(record, work)
            self._check_field(record, "385", {
                "a": term,
                "2": "tlctarget",
            })

    def test_add_series(self):
        edition = self._edition()
        edition.series = self._str
        edition.series_position = 5
        record = Record()
        Annotator.add_series(record, edition)
        self._check_field(record, "490", {
            "a": edition.series,
            "v": str(edition.series_position),
        }, ["0", " "])

        # If there's no series position, the same field is used without
        # the v subfield.
        edition.series_position = None
        record = Record()
        Annotator.add_series(record, edition)
        self._check_field(record, "490", {
            "a": edition.series,
        }, ["0", " "])
        [field] = record.get_fields("490")
        eq_([], field.get_subfields("v"))

        # If there's no series, the field is left out.
        edition.series = None
        record = Record()
        Annotator.add_series(record, edition)
        eq_([], record.get_fields("490"))

    def test_add_system_details(self):
        record = Record()
        Annotator.add_system_details(record)
        self._check_field(record, "538", {"a": "Mode of access: World Wide Web."})

    def test_add_formats(self):
        edition, pool = self._edition(with_license_pool=True)
        epub_no_drm, ignore = DeliveryMechanism.lookup(
            self._db, Representation.EPUB_MEDIA_TYPE, DeliveryMechanism.NO_DRM)
        pool.delivery_mechanisms[0].delivery_mechanism = epub_no_drm
        LicensePoolDeliveryMechanism.set(
            pool.data_source, pool.identifier, Representation.PDF_MEDIA_TYPE,
            DeliveryMechanism.ADOBE_DRM, RightsStatus.IN_COPYRIGHT)

        record = Record()
        Annotator.add_formats(record, pool)
        fields = record.get_fields("538")
        eq_(2, len(fields))
        [pdf, epub] = sorted(fields, key=lambda x: x.get_subfields("a")[0])
        eq_("Adobe PDF eBook", pdf.get_subfields("a")[0])
        eq_([" ", " "], pdf.indicators)
        eq_("EPUB eBook", epub.get_subfields("a")[0])
        eq_([" ", " "], epub.indicators)

    def test_add_summary(self):
        work = self._work(with_license_pool=True)
        work.summary_text = "<p>Summary</p>"

        record = Record()
        Annotator.add_summary(record, work)
        self._check_field(record, "520", {"a": "Summary"})

        # It also works with a materialized work.
        self.add_to_materialized_view([work])
        [mw] = self._db.query(MaterializedWorkWithGenre).all()

        record = Record()
        Annotator.add_summary(record, mw)
        self._check_field(record, "520", {"a": "Summary"})

    def test_add_simplified_genres(self):
        work = self._work(with_license_pool=True)
        fantasy, ignore = Genre.lookup(self._db, "Fantasy", autocreate=True)
        romance, ignore = Genre.lookup(self._db, "Romance", autocreate=True)
        work.genres = [fantasy, romance]

        record = Record()
        Annotator.add_simplified_genres(record, work)
        fields = record.get_fields("650")
        [fantasy_field, romance_field] = sorted(fields, key=lambda x: x.get_subfields("a")[0])
        eq_(["0", "7"], fantasy_field.indicators)
        eq_("Fantasy", fantasy_field.get_subfields("a")[0])
        eq_("Library Simplified", fantasy_field.get_subfields("2")[0])
        eq_(["0", "7"], romance_field.indicators)
        eq_("Romance", romance_field.get_subfields("a")[0])
        eq_("Library Simplified", romance_field.get_subfields("2")[0])

        # It also works with a materialized work.
        self.add_to_materialized_view([work])
        # The work is in the materialized view twice since it has two genres,
        # but we can use either one.
        [mw, ignore] = self._db.query(MaterializedWorkWithGenre).all()

        record = Record()
        Annotator.add_simplified_genres(record, mw)
        fields = record.get_fields("650")
        [fantasy_field, romance_field] = sorted(fields, key=lambda x: x.get_subfields("a")[0])
        eq_(["0", "7"], fantasy_field.indicators)
        eq_("Fantasy", fantasy_field.get_subfields("a")[0])
        eq_("Library Simplified", fantasy_field.get_subfields("2")[0])
        eq_(["0", "7"], romance_field.indicators)
        eq_("Romance", romance_field.get_subfields("a")[0])
        eq_("Library Simplified", romance_field.get_subfields("2")[0])

    def test_add_ebooks_subject(self):
        record = Record()
        Annotator.add_ebooks_subject(record)
        self._check_field(record, "655", {"a": "Electronic books."}, [" ", "0"])

class TestMARCExporter(DatabaseTest):

    def _integration(self):
        return self._external_integration(
            ExternalIntegration.MARC_EXPORT,
            ExternalIntegration.CATALOG_GOAL,
            libraries=[self._default_library])

    def test_from_config(self):
        assert_raises(CannotLoadConfiguration, MARCExporter.from_config, self._default_library)

        integration = self._integration()
        exporter = MARCExporter.from_config(self._default_library)
        eq_(integration, exporter.integration)
        eq_(self._default_library, exporter.library)

        other_library = self._library()
        assert_raises(CannotLoadConfiguration, MARCExporter.from_config, other_library)

    def test_create_record(self):
        work = self._work(with_license_pool=True, title="old title",
                          authors=["old author"], data_source_name=DataSource.OVERDRIVE)
        annotator = Annotator()

        # The record isn't cached yet, so a new record is created and cached.
        eq_(None, work.marc_record)
        record = MARCExporter.create_record(work, annotator)
        [title_field] = record.get_fields("245")
        eq_("old title", title_field.get_subfields("a")[0])
        [author_field] = record.get_fields("100")
        eq_("author, old", author_field.get_subfields("a")[0])
        [distributor_field] = record.get_fields("264")
        eq_(DataSource.OVERDRIVE, distributor_field.get_subfields("b")[0])
        cached = work.marc_record
        assert "old title" in cached
        assert "author, old" in cached
        # The distributor isn't part of the cached record.
        assert DataSource.OVERDRIVE not in cached

        work.presentation_edition.title = "new title"
        work.presentation_edition.sort_author = "author, new"
        new_data_source = DataSource.lookup(self._db, DataSource.BIBLIOTHECA)
        work.license_pools[0].data_source = new_data_source

        # Now that the record is cached, creating a record will
        # use the cache. Distributor will be updated since it's
        # not part of the cached record.
        record = MARCExporter.create_record(work, annotator)
        [title_field] = record.get_fields("245")
        eq_("old title", title_field.get_subfields("a")[0])
        [author_field] = record.get_fields("100")
        eq_("author, old", author_field.get_subfields("a")[0])
        [distributor_field] = record.get_fields("264")
        eq_(DataSource.BIBLIOTHECA, distributor_field.get_subfields("b")[0])

        # But we can force an update to the cached record.
        record = MARCExporter.create_record(work, annotator, force_create=True)
        [title_field] = record.get_fields("245")
        eq_("new title", title_field.get_subfields("a")[0])
        [author_field] = record.get_fields("100")
        eq_("author, new", author_field.get_subfields("a")[0])
        [distributor_field] = record.get_fields("264")
        eq_(DataSource.BIBLIOTHECA, distributor_field.get_subfields("b")[0])
        cached = work.marc_record
        assert "old title" not in cached
        assert "author, old" not in cached
        assert "new title" in cached
        assert "author, new" in cached

        # If we pass in an integration, it's passed along to the annotator.
        integration = self._integration()
        class MockAnnotator(Annotator):
            integration = None
            def annotate_work_record(self, work, pool, edition, identifier, record, integration):
                self.integration = integration

        annotator = MockAnnotator()
        record = MARCExporter.create_record(work, annotator, integration=integration)
        eq_(integration, annotator.integration)

    def test_records(self):
        self._integration()
        exporter = MARCExporter.from_config(self._default_library)
        annotator = Annotator()
        lane = self._lane("Test Lane", genres=["Mystery"])
        w1 = self._work(genre="Mystery", with_open_access_download=True)
        w2 = self._work(genre="Mystery", with_open_access_download=True)
        self.add_to_materialized_view([w1, w2])

        content = StringIO()
        content.write(exporter.records(lane, annotator))
        records = list(MARCReader(content.getvalue()))
        eq_(2, len(records))

        title_fields = [record.get_fields("245") for record in records]
        titles = [fields[0].get_subfields("a")[0] for fields in title_fields]
        eq_(set([w1.title, w2.title]), set(titles))

        assert w1.title in w1.marc_record
        assert w2.title in w2.marc_record

        content.close()

    def test_records_mirrors_files_if_storage_configured(self):
        integration = self._integration()
        exporter = MARCExporter.from_config(self._default_library)
        annotator = Annotator()
        lane = self._lane("Test Lane", genres=["Mystery"])
        w1 = self._work(genre="Mystery", with_open_access_download=True)
        w2 = self._work(genre="Mystery", with_open_access_download=True)
        self.add_to_materialized_view([w1, w2])

        integration.setting(MARCExporter.STORAGE_PROTOCOL).value = ExternalIntegration.S3

        # If there's a storage protocol but not corresponding storage integration,
        # it raises an exception.
        assert_raises(Exception, exporter.records, lane, annotator)
        
        # If there is a storage integration, the output file is mirrored.
        mirror_integration = self._external_integration(
            ExternalIntegration.S3, ExternalIntegration.STORAGE_GOAL,
            username="username", password="password",
        )

        mirror = MockS3Uploader()
        content = exporter.records(lane, annotator, mirror=mirror)

        eq_(1, len(mirror.uploaded))
        eq_(content, mirror.content[0])
        eq_("https://s3.amazonaws.com/test.marc.bucket/%s/%s.mrc" % (self._default_library.short_name, urllib.quote_plus(lane.display_name)),
            mirror.uploaded[0].mirror_url)

        # A CachedMARCFile was created to track the mirrored file.
        [cache] = self._db.query(CachedMARCFile).all()
        eq_(self._default_library, cache.library)
        eq_(lane, cache.lane)
        eq_(mirror.uploaded[0], cache.representation)
        eq_(None, cache.representation.content)
        self._db.delete(cache)

        # It also works with a WorkList instead of a Lane, in which case
        # there will be no lane in the CachedMARCFile.
        worklist = WorkList()
        worklist.initialize(self._default_library, display_name="All Books")

        mirror = MockS3Uploader()
        content = exporter.records(worklist, annotator, mirror=mirror)

        eq_(1, len(mirror.uploaded))
        eq_(content, mirror.content[0])
        eq_("https://s3.amazonaws.com/test.marc.bucket/%s/%s.mrc" % (self._default_library.short_name, urllib.quote_plus(worklist.display_name)),
            mirror.uploaded[0].mirror_url)

        [cache] = self._db.query(CachedMARCFile).all()
        eq_(self._default_library, cache.library)
        eq_(None, cache.lane)
        eq_(mirror.uploaded[0], cache.representation)
        eq_(None, cache.representation.content)
