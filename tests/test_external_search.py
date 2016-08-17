from nose.tools import (
    eq_,
    set_trace,
)
import logging
import time
from psycopg2.extras import NumericRange

from . import (
    DatabaseTest,
)
from config import (
    temp_config,
    Configuration,
)

from lane import Lane
from model import Edition
from external_search import (
    ExternalSearchIndex,
    DummyExternalSearchIndex,
)
from classifier import Classifier


class TestExternalSearch(DatabaseTest):
    """
    These tests require elasticsearch to be running locally. If it's not, or there's
    an error creating the index, the tests will pass without doing anything.

    Tests for elasticsearch are useful for ensuring that we haven't accidentally broken
    a type of search by changing analyzers or queries, but search needs to be tested manually
    to ensure that it works well overall, with a realistic index.
    """

    def setup(self):
        super(TestExternalSearch, self).setup()
        with temp_config() as config:
            config[Configuration.INTEGRATIONS][Configuration.ELASTICSEARCH_INTEGRATION] = {}
            config[Configuration.INTEGRATIONS][Configuration.ELASTICSEARCH_INTEGRATION][Configuration.URL] = "http://localhost:9200"
            config[Configuration.INTEGRATIONS][Configuration.ELASTICSEARCH_INTEGRATION][Configuration.ELASTICSEARCH_INDEX_KEY] = "test_index"

            try:
                ExternalSearchIndex.__client = None
                self.search = ExternalSearchIndex()
                # Start with an empty index
                self.search.setup_index()
            except Exception as e:
                self.search = None
                print "Unable to set up elasticsearch index, search tests will be skipped."
                print e

        if self.search:
            works = []

            self.moby_dick = self._work(title="Moby Dick", authors="Herman Melville", fiction=True)
            self.moby_dick.presentation_edition.subtitle = "Or, the Whale"
            self.moby_dick.presentation_edition.series = "Classics"
            self.moby_dick.summary_text = "Ishmael"
            self.moby_dick.presentation_edition.publisher = "Project Gutenberg"
            self.moby_dick.set_presentation_ready()
            works.append(self.moby_dick)

            self.moby_duck = self._work(title="Moby Duck", authors="Donovan Hohn", fiction=False)
            self.moby_duck.presentation_edition.subtitle = "The True Story of 28,800 Bath Toys Lost at Sea"
            self.moby_duck.summary_text = "A compulsively readable narrative"
            self.moby_duck.presentation_edition.publisher = "Penguin"
            self.moby_duck.set_presentation_ready()
            works.append(self.moby_duck)

            self.title_match = self._work(title="Match")
            self.title_match.set_presentation_ready()
            works.append(self.title_match)

            self.subtitle_match = self._work()
            self.subtitle_match.presentation_edition.subtitle = "Match"
            self.subtitle_match.set_presentation_ready()
            works.append(self.subtitle_match)

            self.summary_match = self._work()
            self.summary_match.summary_text = "Match"
            self.summary_match.set_presentation_ready()
            works.append(self.summary_match)
        
            self.publisher_match = self._work()
            self.publisher_match.presentation_edition.publisher = "Match"
            self.publisher_match.set_presentation_ready()
            works.append(self.publisher_match)

            self.tess = self._work(title="Tess of the d'Urbervilles")
            self.tess.set_presentation_ready()
            works.append(self.tess)

            self.tiffany = self._work(title="Breakfast at Tiffany's")
            self.tiffany.set_presentation_ready()
            works.append(self.tiffany)
            
            self.les_mis = self._work()
            self.les_mis.presentation_edition.title = u"Les Mis\u00E9rables"
            self.les_mis.set_presentation_ready()
            works.append(self.les_mis)

            self.lincoln = self._work(genre="Biography & Memoir", title="Abraham Lincoln")
            self.lincoln.set_presentation_ready()
            works.append(self.lincoln)

            self.washington = self._work(genre="Biography", title="George Washington")
            self.washington.set_presentation_ready()
            works.append(self.washington)

            self.lincoln_vampire = self._work(title="Abraham Lincoln: Vampire Hunter", genre="Fantasy")
            self.lincoln_vampire.set_presentation_ready()
            works.append(self.lincoln_vampire)

            self.children_work = self._work(title="Alice in Wonderland", audience=Classifier.AUDIENCE_CHILDREN)
            self.children_work.set_presentation_ready()
            works.append(self.children_work)

            self.ya_work = self._work(title="Go Ask Alice", audience=Classifier.AUDIENCE_YOUNG_ADULT)
            self.ya_work.set_presentation_ready()
            works.append(self.ya_work)

            self.adult_work = self._work(title="Still Alice", audience=Classifier.AUDIENCE_ADULT)
            self.adult_work.set_presentation_ready()
            works.append(self.adult_work)

            self.ya_romance = self._work(audience=Classifier.AUDIENCE_YOUNG_ADULT, genre="Romance")
            self.ya_romance.set_presentation_ready()
            works.append(self.ya_romance)

            self.no_age = self._work()
            self.no_age.summary_text = "President Barack Obama's election in 2008 energized the United States"
            self.no_age.set_presentation_ready()
            works.append(self.no_age)

            self.age_4_5 = self._work()
            self.age_4_5.target_age = NumericRange(4, 5, '[]')
            self.age_4_5.summary_text = "President Barack Obama's election in 2008 energized the United States"
            self.age_4_5.set_presentation_ready()
            works.append(self.age_4_5)

            self.age_5_6 = self._work(fiction=False)
            self.age_5_6.target_age = NumericRange(5, 6, '[]')
            self.age_5_6.set_presentation_ready()
            works.append(self.age_5_6)

            self.obama = self._work(genre="Biography & Memoir")
            self.obama.target_age = NumericRange(8, 8, '[]')
            self.obama.summary_text = "President Barack Obama's election in 2008 energized the United States"
            self.obama.set_presentation_ready()
            works.append(self.obama)

            self.dodger = self._work()
            self.dodger.target_age = NumericRange(8, 8, '[]')
            self.dodger.summary_text = "Willie finds himself running for student council president"
            self.dodger.set_presentation_ready()
            works.append(self.dodger)

            self.age_9_10 = self._work()
            self.age_9_10.target_age = NumericRange(9, 10, '[]')
            self.age_9_10.summary_text = "President Barack Obama's election in 2008 energized the United States"
            self.age_9_10.set_presentation_ready()
            works.append(self.age_9_10)

            self.age_2_10 = self._work()
            self.age_2_10.target_age = NumericRange(2, 10, '[]')
            self.age_2_10.set_presentation_ready()
            works.append(self.age_2_10)

            self.pride = self._work(title="Pride and Prejudice")
            self.pride.presentation_edition.medium = Edition.BOOK_MEDIUM
            self.pride.set_presentation_ready()
            works.append(self.pride)

            self.pride_audio = self._work(title="Pride and Prejudice")
            self.pride_audio.presentation_edition.medium = Edition.AUDIO_MEDIUM
            self.pride_audio.set_presentation_ready()
            works.append(self.pride_audio)

            self.sherlock = self._work(title="The Adventures of Sherlock Holmes")
            self.sherlock.presentation_edition.language = "en"
            self.sherlock.set_presentation_ready()
            works.append(self.sherlock)

            self.sherlock_spanish = self._work(title="Las Aventuras de Sherlock Holmes")
            self.sherlock_spanish.presentation_edition.language = "es"
            self.sherlock_spanish.set_presentation_ready()
            works.append(self.sherlock_spanish)

            self.suppressed = self._work(with_license_pool=True, title="Suppressed")
            self.suppressed.license_pools[0].suppressed = True
            self.suppressed.set_presentation_ready()
            works.append(self.suppressed)

            self.no_licenses_owned = self._work(with_license_pool=True, title="NoLicensesOwned")
            self.no_licenses_owned.license_pools[0].open_access = False
            self.no_licenses_owned.license_pools[0].licenses_owned = 0
            self.no_licenses_owned.set_presentation_ready()
            works.append(self.no_licenses_owned)

            self.open_access = self._work(with_license_pool=True, title="OpenAccess")
            self.open_access.license_pools[0].open_access = True
            self.open_access.set_presentation_ready()
            works.append(self.open_access)

            self.licenses_available = self._work(with_license_pool=True, title="LotsOfLicenses")
            self.licenses_available.license_pools[0].open_access = False
            self.licenses_available.license_pools[0].licenses_owned = 20
            self.licenses_available.license_pools[0].licenses_available = 20
            self.licenses_available.set_presentation_ready()
            works.append(self.licenses_available)

            self.no_licenses_available = self._work(with_license_pool=True, title="NoLicensesAvailable")
            self.no_licenses_available.license_pools[0].open_access = False
            self.no_licenses_available.license_pools[0].licenses_owned = 1
            self.no_licenses_available.license_pools[0].licenses_available = 0
            self.no_licenses_available.set_presentation_ready()
            works.append(self.no_licenses_available)

            self.search.bulk_update(works)

            time.sleep(5)

    def teardown(self):
        if self.search:
            self.search.indices.delete(self.search.works_index)
            ExternalSearchIndex.__client = None
        super(TestExternalSearch, self).teardown()

    def test_query_works(self):
        """
        These are all in one method because the setup is expensive.
        """
        if not self.search:
            return

        # Pagination

        results = self.search.query_works("moby dick", None, None, None, None, None, None, None, size=1, offset=0, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.moby_dick.id), hits[0]["_id"])

        results = self.search.query_works("moby dick", None, None, None, None, None, None, None, size=1, offset=1, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.moby_duck.id), hits[0]["_id"])

        results = self.search.query_works("moby dick", None, None, None, None, None, None, None, size=2, offset=0, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.moby_dick.id), hits[0]["_id"])


        # Matches all main fields

        title_results = self.search.query_works("moby", None, None, None, None, None, None, None, only_deliverable=False)
        eq_(2, len(title_results["hits"]["hits"]))

        author_results = self.search.query_works("melville", None, None, None, None, None, None, None, only_deliverable=False)
        eq_(1, len(author_results["hits"]["hits"]))

        subtitle_results = self.search.query_works("whale", None, None, None, None, None, None, None, only_deliverable=False)
        eq_(1, len(subtitle_results["hits"]["hits"]))

        series_results = self.search.query_works("classics", None, None, None, None, None, None, None, only_deliverable=False)
        eq_(1, len(series_results["hits"]["hits"]))

        summary_results = self.search.query_works("ishmael", None, None, None, None, None, None, None, only_deliverable=False)
        eq_(1, len(summary_results["hits"]["hits"]))

        publisher_results = self.search.query_works("gutenberg", None, None, None, None, None, None, None, only_deliverable=False)
        eq_(1, len(summary_results["hits"]["hits"]))


        # Ranks title above subtitle above summary above publisher

        results = self.search.query_works("match", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(4, len(hits))
        eq_(unicode(self.title_match.id), hits[0]['_id'])
        eq_(unicode(self.subtitle_match.id), hits[1]['_id'])
        eq_(unicode(self.summary_match.id), hits[2]['_id'])
        eq_(unicode(self.publisher_match.id), hits[3]['_id'])
        

        # Ranks both title and author higher than only title

        results = self.search.query_works("moby melville", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.moby_dick.id), hits[0]['_id'])
        eq_(unicode(self.moby_duck.id), hits[1]['_id'])


        # Matches a quoted phrase

        results = self.search.query_works("\"moby dick\"", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.moby_dick.id), hits[0]["_id"])


        # Matches stemmed word

        results = self.search.query_works("runs", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.dodger.id), hits[0]['_id'])


        # Matches misspelled phrase

        results = self.search.query_works("movy", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))

        results = self.search.query_works("mleville", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))

        results = self.search.query_works("mo by dick", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))


        # Matches word with apostrophe

        results = self.search.query_works("durbervilles", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.tess.id), hits[0]['_id'])

        results = self.search.query_works("tiffanys", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.tiffany.id), hits[0]['_id'])


        # Matches work with unicode character

        results = self.search.query_works("les miserables", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.les_mis.id), hits[0]['_id'])


        # Matches fiction

        results = self.search.query_works("fiction moby", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.moby_dick.id), hits[0]['_id'])

        results = self.search.query_works("nonfiction moby", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.moby_duck.id), hits[0]['_id'])


        # Matches genre

        results = self.search.query_works("romance", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.ya_romance.id), hits[0]['_id'])


        # Matches audience

        results = self.search.query_works("children's", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.children_work.id), hits[0]['_id'])

        results = self.search.query_works("young adult", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        work_ids = sorted([unicode(self.ya_work.id), unicode(self.ya_romance.id)])
        result_ids = sorted([hit["_id"] for hit in hits])
        eq_(work_ids, result_ids)


        # Matches grade

        results = self.search.query_works("grade 4", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.age_9_10.id), hits[0]['_id'])
        
        results = self.search.query_works("grade 4-6", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.age_9_10.id), hits[0]['_id'])


        # Matches age

        results = self.search.query_works("age 9", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.age_9_10.id), hits[0]['_id'])
        
        results = self.search.query_works("age 10-12", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.age_9_10.id), hits[0]['_id'])


        # Ranks closest target age range highest

        results = self.search.query_works("age 3-5", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(3, len(hits))
        eq_(unicode(self.age_4_5.id), hits[0]['_id'])
        eq_(unicode(self.age_5_6.id), hits[1]['_id'])
        eq_(unicode(self.age_2_10.id), hits[2]['_id'])


        # Matches genre + audience

        results = self.search.query_works("young adult romance", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.ya_romance.id), hits[0]['_id'])


        # Matches age + fiction

        results = self.search.query_works("age 5 fiction", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.age_4_5.id), hits[0]['_id'])


        # Matches genre + title

        results = self.search.query_works("lincoln biography", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        eq_(unicode(self.lincoln.id), hits[0]['_id'])
        eq_(unicode(self.lincoln_vampire.id), hits[1]['_id'])


        # Matches age + genre + summary

        results = self.search.query_works("age 8 president biography", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(5, len(hits))
        eq_(unicode(self.obama.id), hits[0]['_id'])


        # Filters on media

        book_lane = Lane(self._db, "Books", media=Edition.BOOK_MEDIUM)
        audio_lane = Lane(self._db, "Audio", media=Edition.AUDIO_MEDIUM)

        results = self.search.query_works("pride and prejudice", book_lane.media, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.pride.id), hits[0]["_id"])

        results = self.search.query_works("pride and prejudice", audio_lane.media, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.pride_audio.id), hits[0]["_id"])


        # Filters on languages

        english_lane = Lane(self._db, "English", languages="en")
        spanish_lane = Lane(self._db, "Spanish", languages="es")
        both_lane = Lane(self._db, "Both", languages=["en", "es"])

        results = self.search.query_works("sherlock", None, english_lane.languages, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.sherlock.id), hits[0]["_id"])

        results = self.search.query_works("sherlock", None, spanish_lane.languages, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.sherlock_spanish.id), hits[0]["_id"])

        results = self.search.query_works("sherlock", None, both_lane.languages, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))


        # Filters on exclude languages

        no_english_lane = Lane(self._db, "English", exclude_languages="en")
        no_spanish_lane = Lane(self._db, "Spanish", exclude_languages="es")
        neither_lane = Lane(self._db, "Both", exclude_languages=["en", "es"])

        results = self.search.query_works("sherlock", None, None, no_english_lane.exclude_languages, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.sherlock_spanish.id), hits[0]["_id"])

        results = self.search.query_works("sherlock", None, None, no_spanish_lane.exclude_languages, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.sherlock.id), hits[0]["_id"])

        results = self.search.query_works("sherlock", None, None, neither_lane.exclude_languages, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(0, len(hits))
        

        # Filters on fiction

        fiction_lane = Lane(self._db, "fiction", fiction=True)
        nonfiction_lane = Lane(self._db, "nonfiction", fiction=False)
        both_lane = Lane(self._db, "both", fiction=Lane.BOTH_FICTION_AND_NONFICTION)

        results = self.search.query_works("moby dick", None, None, None, fiction_lane.fiction, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.moby_dick.id), hits[0]["_id"])

        results = self.search.query_works("moby dick", None, None, None, nonfiction_lane.fiction, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.moby_duck.id), hits[0]["_id"])

        results = self.search.query_works("moby dick", None, None, None, both_lane.fiction, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))


        # Filters on audience

        adult_lane = Lane(self._db, "Adult", audiences=Classifier.AUDIENCE_ADULT)
        ya_lane = Lane(self._db, "YA", audiences=Classifier.AUDIENCE_YOUNG_ADULT)
        children_lane = Lane(self._db, "Children", audiences=Classifier.AUDIENCE_CHILDREN)
        ya_and_children_lane = Lane(self._db, "YA and Children", audiences=[Classifier.AUDIENCE_YOUNG_ADULT, Classifier.AUDIENCE_CHILDREN])

        results = self.search.query_works("alice", None, None, None, None, adult_lane.audiences, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.adult_work.id), hits[0]["_id"])

        results = self.search.query_works("alice", None, None, None, None, ya_lane.audiences, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.ya_work.id), hits[0]["_id"])

        results = self.search.query_works("alice", None, None, None, None, children_lane.audiences, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.children_work.id), hits[0]["_id"])

        results = self.search.query_works("alice", None, None, None, None, ya_and_children_lane.audiences, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))
        work_ids = sorted([unicode(self.ya_work.id), unicode(self.children_work.id)])
        result_ids = sorted([hit["_id"] for hit in hits])
        eq_(work_ids, result_ids)


        # Filters on age range

        age_8_lane = Lane(self._db, "Age 8", age_range=[8, 8])
        age_5_8_lane = Lane(self._db, "Age 5-8", age_range=[5, 8])
        age_5_10_lane = Lane(self._db, "Age 5-10", age_range=[5, 10])
        age_8_10_lane = Lane(self._db, "Age 8-10", age_range=[8, 10])

        results = self.search.query_works("president", None, None, None, None, None, age_8_lane.age_range, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(3, len(hits))
        work_ids = sorted([unicode(self.no_age.id), unicode(self.obama.id), unicode(self.dodger.id)])
        result_ids = sorted([hit["_id"] for hit in hits])
        eq_(work_ids, result_ids)

        results = self.search.query_works("president", None, None, None, None, None, age_5_8_lane.age_range, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(4, len(hits))
        work_ids = sorted([unicode(self.no_age.id),
                           unicode(self.age_4_5.id),
                           unicode(self.obama.id),
                           unicode(self.dodger.id)])
        result_ids = sorted([hit["_id"] for hit in hits])
        eq_(work_ids, result_ids)

        results = self.search.query_works("president", None, None, None, None, None, age_5_10_lane.age_range, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(5, len(hits))
        work_ids = sorted([unicode(self.no_age.id),
                           unicode(self.age_4_5.id),
                           unicode(self.obama.id),
                           unicode(self.dodger.id),
                           unicode(self.age_9_10.id)])
        result_ids = sorted([hit["_id"] for hit in hits])
        eq_(work_ids, result_ids)

        results = self.search.query_works("president", None, None, None, None, None, age_8_10_lane.age_range, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(4, len(hits))
        work_ids = sorted([unicode(self.no_age.id),
                           unicode(self.obama.id),
                           unicode(self.dodger.id),
                           unicode(self.age_9_10.id)])
        result_ids = sorted([hit["_id"] for hit in hits])
        eq_(work_ids, result_ids)


        # Filters on genre

        biography_lane = Lane(self._db, "Biography", genres=["Biography & Memoir"])
        fantasy_lane = Lane(self._db, "Fantasy", genres=["Fantasy"])
        both_lane = Lane(self._db, "Both", genres=["Biography & Memoir", "Fantasy"], fiction=Lane.BOTH_FICTION_AND_NONFICTION)

        results = self.search.query_works("lincoln", None, None, None, None, None, None, biography_lane.genre_ids, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.lincoln.id), hits[0]["_id"])

        results = self.search.query_works("lincoln", None, None, None, None, None, None, fantasy_lane.genre_ids, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))
        eq_(unicode(self.lincoln_vampire.id), hits[0]["_id"])

        results = self.search.query_works("lincoln", None, None, None, None, None, None, both_lane.genre_ids, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(2, len(hits))


        # Filters out works that aren't deliverable if only_deliverable is True

        # Suppressed works aren't deliverable

        results = self.search.query_works("suppressed", None, None, None, None, None, None, None, only_deliverable=True)
        hits = results["hits"]["hits"]
        eq_(0, len(hits))

        results = self.search.query_works("suppressed", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))

        # Works with no licenses owned aren't deliverable

        results = self.search.query_works("nolicensesowned", None, None, None, None, None, None, None, only_deliverable=True)
        hits = results["hits"]["hits"]
        eq_(0, len(hits))

        results = self.search.query_works("nolicensesowned", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))

        # Open access works are always deliverable

        results = self.search.query_works("openaccess", None, None, None, None, None, None, None, only_deliverable=True)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))

        results = self.search.query_works("openaccess", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))

        # Works with licenses owned and available are deliverable

        results = self.search.query_works("lotsoflicenses", None, None, None, None, None, None, None, only_deliverable=True)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))

        results = self.search.query_works("lotsoflicenses", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))

        # Works with licenses owned but not available may be deliverable, depending on the hold policy

        results = self.search.query_works("nolicensesavailable", None, None, None, None, None, None, None, only_deliverable=True)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))

        results = self.search.query_works("nolicensesavailable", None, None, None, None, None, None, None, only_deliverable=False)
        hits = results["hits"]["hits"]
        eq_(1, len(hits))

        with temp_config() as config:
            config[Configuration.POLICIES] = {
                Configuration.HOLD_POLICY: Configuration.HOLD_POLICY_HIDE
            }

            results = self.search.query_works("nolicensesavailable", None, None, None, None, None, None, None, only_deliverable=True)
            hits = results["hits"]["hits"]
            eq_(0, len(hits))
            
            results = self.search.query_works("nolicensesavailable", None, None, None, None, None, None, None, only_deliverable=False)
            hits = results["hits"]["hits"]
            eq_(1, len(hits))

        
class TestSearchQuery(DatabaseTest):
    def test_make_query(self):

        search = DummyExternalSearchIndex()

        # Basic query
        query = search.make_query("test")

        must = query['dis_max']['queries']

        eq_(3, len(must))
        stemmed_query = must[0]['simple_query_string']
        eq_("test", stemmed_query['query'])
        assert "title^4" in stemmed_query['fields']
        assert 'publisher' in stemmed_query['fields']

        phrase_queries = must[1]['bool']['should']
        eq_(3, len(phrase_queries))
        title_phrase_query = phrase_queries[0]['match_phrase']
        assert 'title.minimal' in title_phrase_query
        eq_("test", title_phrase_query['title.minimal'])

        # Query with fuzzy blacklist keyword
        query = search.make_query("basketball")

        must = query['dis_max']['queries']

        eq_(2, len(must))

        # Query with genre
        query = search.make_query("test romance")

        must = query['dis_max']['queries']

        eq_(4, len(must))
        full_query = must[0]['simple_query_string']
        eq_("test romance", full_query['query'])
        assert "title^4" in full_query['fields']
        assert 'publisher' in full_query['fields']

        classification_query = must[3]['bool']['must']
        eq_(2, len(classification_query))
        genre_query = classification_query[0]['match']
        assert 'genres.name' in genre_query
        eq_('Romance', genre_query['genres.name'])
        remaining_query = classification_query[1]['simple_query_string']
        assert "test" in remaining_query['query']
        assert "romance" not in remaining_query['query']
        assert 'author^4' in remaining_query['fields']


        # Query with fiction
        query = search.make_query("test nonfiction")
        
        must = query['dis_max']['queries']

        eq_(4, len(must))

        classification_query = must[3]['bool']['must']
        eq_(2, len(classification_query))
        fiction_query = classification_query[0]['match']
        assert 'fiction' in fiction_query
        eq_('Nonfiction', fiction_query['fiction'])
        remaining_query = classification_query[1]['simple_query_string']
        assert "test" in remaining_query['query']
        assert "fiction" not in remaining_query['query']
        assert 'author^4' in remaining_query['fields']
        

        # Query with genre and fiction
        query = search.make_query("test romance fiction")

        must = query['dis_max']['queries']

        eq_(4, len(must))

        classification_query = must[3]['bool']['must']
        eq_(3, len(classification_query))
        genre_query = classification_query[0]['match']
        assert 'genres.name' in genre_query
        eq_('Romance', genre_query['genres.name'])
        fiction_query = classification_query[1]['match']
        assert 'fiction' in fiction_query
        eq_('Fiction', fiction_query['fiction'])
        remaining_query = classification_query[2]['simple_query_string']
        assert "test" in remaining_query['query']
        assert "romance" not in remaining_query['query']
        assert "fiction" not in remaining_query['query']
        assert 'author^4' in remaining_query['fields']

        # Query with audience
        query = search.make_query("test young adult")

        must = query['dis_max']['queries']

        eq_(4, len(must))
        full_query = must[0]['simple_query_string']
        eq_("test young adult", full_query['query'])

        classification_query = must[3]['bool']['must']
        eq_(2, len(classification_query))
        audience_query = classification_query[0]['match']
        assert 'audience' in audience_query
        eq_('YoungAdult', audience_query['audience'])
        remaining_query = classification_query[1]['simple_query_string']
        assert "test" in remaining_query['query']
        assert "young" not in remaining_query['query']
        
        # Query with grade
        query = search.make_query("test grade 6")
        
        must = query['dis_max']['queries']

        eq_(4, len(must))
        full_query = must[0]['simple_query_string']
        eq_("test grade 6", full_query['query'])

        classification_query = must[3]['bool']['must']
        eq_(2, len(classification_query))
        grade_query = classification_query[0]['bool']
        assert 'must' in grade_query
        assert 'should' in grade_query
        age_must = grade_query['must']
        eq_(2, len(age_must))
        eq_(11, age_must[0]['range']['target_age.upper']['gte'])
        eq_(11, age_must[1]['range']['target_age.lower']['lte'])

        remaining_query = classification_query[1]['simple_query_string']
        assert "test" in remaining_query['query']
        assert "grade" not in remaining_query['query']
        
        # Query with age
        query = search.make_query("test 5-10 years")

        must = query['dis_max']['queries']

        eq_(4, len(must))
        full_query = must[0]['simple_query_string']
        eq_("test 5-10 years", full_query['query'])

        classification_query = must[3]['bool']['must']
        eq_(2, len(classification_query))
        grade_query = classification_query[0]['bool']
        assert 'must' in grade_query
        assert 'should' in grade_query
        age_must = grade_query['must']
        eq_(2, len(age_must))
        eq_(5, age_must[0]['range']['target_age.upper']['gte'])
        eq_(10, age_must[1]['range']['target_age.lower']['lte'])

        remaining_query = classification_query[1]['simple_query_string']
        assert "test" in remaining_query['query']
        assert "5" not in remaining_query['query']
        assert "years" not in remaining_query['query']

class TestSearchFilter(DatabaseTest):
        
    def test_filter_from_lane_definition_handles_age_range(self):
        search = DummyExternalSearchIndex()

        lane = Lane(
            self._db, "For Ages 5-10", 
            age_range=[5,10]
        )
        filter = search.make_filter(
            lane.media, lane.languages, lane.exclude_languages,
            lane.fiction, list(lane.audiences), lane.age_range,
            lane.genre_ids,
            only_deliverable=False,
        )

        medium_filter, audience_filter, target_age_filter = filter['and']
        upper_filter, lower_filter = target_age_filter['and']
        expect_upper = {'or': [{'range': {'target_age.upper': {'gte': 5}}}, {'bool': {'must_not': {'exists': {'field': 'target_age.upper'}}}}]}
        expect_lower = {'or': [{'range': {'target_age.lower': {'lte': 10}}}, {'bool': {'must_not': {'exists': {'field': 'target_age.lower'}}}}]}
        eq_(expect_upper, upper_filter)
        eq_(expect_lower, lower_filter)

    def test_filter_from_lane_definition_handles_languages(self):
        search = DummyExternalSearchIndex()

        lane = Lane(
            self._db, "english or spanish", 
            languages=set(['eng', 'spa']),
        )
        filter = search.make_filter(
            lane.media, lane.languages, lane.exclude_languages,
            lane.fiction, list(lane.audiences), lane.age_range,
            lane.genre_ids,
            only_deliverable=False,
        )
        
        languages_filter, medium_filter = filter['and']
        expect_languages = ['eng', 'spa']
        assert 'terms' in languages_filter
        assert 'language' in languages_filter['terms']
        eq_(expect_languages, sorted(languages_filter['terms']['language']))

    def test_filter_from_lane_definition_handles_exclude_languages(self):
        search = DummyExternalSearchIndex()

        lane = Lane(
            self._db, "Not english or spanish", 
            exclude_languages=set(['eng', 'spa']),
        )
        filter = search.make_filter(
            lane.media, lane.languages, lane.exclude_languages,
            lane.fiction, list(lane.audiences), lane.age_range,
            lane.genre_ids,
            only_deliverable=False,
        )
        
        exclude_languages_filter, medium_filter = filter['and']
        expect_exclude_languages = ['eng', 'spa']
        assert 'not' in exclude_languages_filter
        assert 'terms' in exclude_languages_filter['not']
        assert 'language' in exclude_languages_filter['not']['terms']
        eq_(expect_exclude_languages, sorted(exclude_languages_filter['not']['terms']['language']))

    def test_filter_handles_only_deliverable(self):
        search = DummyExternalSearchIndex()

        filter = search.make_filter(None, None, None, None, None, None, None, only_deliverable=True)
        [deliverable_filter] = filter['and']
        assert 'and' in deliverable_filter
        suppressed_filter, licenses_owned_filter = deliverable_filter['and']

        assert 'term' in suppressed_filter
        assert 'license_pools.suppressed' in suppressed_filter['term']
        eq_(False, suppressed_filter['term']['license_pools.suppressed'])
        
        assert 'or' in licenses_owned_filter
        licenses_owned_gte_filter, open_access_filter = licenses_owned_filter['or']

        assert 'range' in licenses_owned_gte_filter
        assert 'license_pools.licenses_owned' in licenses_owned_gte_filter['range']
        assert 'gte' in licenses_owned_gte_filter['range']['license_pools.licenses_owned']
        eq_(1, licenses_owned_gte_filter['range']['license_pools.licenses_owned']['gte'])

        assert 'term' in open_access_filter
        assert 'license_pools.open_access' in open_access_filter['term']
        eq_(True, open_access_filter['term']['license_pools.open_access'])

        with temp_config() as config:
            config[Configuration.POLICIES] = {
                Configuration.HOLD_POLICY: Configuration.HOLD_POLICY_HIDE
            }

            filter = search.make_filter(None, None, None, None, None, None, None, only_deliverable=True)
            [deliverable_filter] = filter['and']
            assert 'and' in deliverable_filter
            available_filter, suppressed_filter, licenses_owned_filter = deliverable_filter['and']

            assert 'or' in available_filter
            licenses_available_filter, open_access_filter = available_filter['or']

            assert 'range' in licenses_available_filter
            assert 'license_pools.licenses_available' in licenses_available_filter['range']
            assert 'gte' in licenses_available_filter['range']['license_pools.licenses_available']
            eq_(1, licenses_available_filter['range']['license_pools.licenses_available']['gte'])
            
            assert 'term' in open_access_filter
            assert 'license_pools.open_access' in open_access_filter['term']
            eq_(True, open_access_filter['term']['license_pools.open_access'])

