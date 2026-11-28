"""Offline regression checks for Resource Discovery. Run with unittest."""
import unittest
from unittest.mock import patch

from resource_discovery.search import (
    fallback_resource, matches_discovery_filters, search_resources,
)
from resource_discovery.discovery_filters import normalize_filters


class DiscoveryRegressionTests(unittest.TestCase):
    def test_all_filter_groups_are_preserved(self):
        groups = ['skills', 'degree_programs', 'career_fields', 'prices',
                  'sources', 'resource_types', 'formats', 'difficulties']
        filters = normalize_filters({group: ['value'] for group in groups})
        self.assertEqual(set(filters), set(groups))
        self.assertTrue(all(filters[group] == ['value'] for group in groups))

    def test_format_excludes_webpages(self):
        filters = normalize_filters({'formats': ['video']})
        self.assertFalse(matches_discovery_filters({'resource_format': 'webpage'}, filters))
        self.assertTrue(matches_discovery_filters({'resource_format': 'video'}, filters))

    def test_combined_filters_require_all_groups(self):
        filters = normalize_filters({'formats': ['video'], 'prices': ['free']})
        self.assertTrue(matches_discovery_filters({'resource_format': 'video', 'pricing_model': None}, filters))
        self.assertTrue(matches_discovery_filters({'resource_format': 'video', 'pricing_model': 'free'}, filters))

    def test_fallback_preserves_description(self):
        resource = fallback_resource({'url': 'https://example.org/tutorial',
                                      'title': 'Tutorial', 'description': 'Learn something useful'})
        self.assertEqual(resource['description'], 'Learn something useful')

    @patch('resource_discovery.search.search_brave')
    @patch('resource_discovery.search.inspect_resource')
    def test_search_filters_inspected_results(self, inspect, brave):
        brave.return_value = [{'url': 'https://example.org/a'}, {'url': 'https://example.org/b'}]
        inspect.side_effect = [
            {'resource_format': 'webpage'}, {'resource_format': 'video'},
        ]
        results = search_resources('python', {'formats': ['video']})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['resource_format'], 'video')


if __name__ == '__main__':
    unittest.main()

class ClassificationPhase2Tests(unittest.TestCase):
    def test_videoobject_is_video(self):
        from bs4 import BeautifulSoup
        from resource_discovery.search import classify_page_format
        soup = BeautifulSoup('<script type="application/ld+json">{"@type":"VideoObject"}</script>', 'html.parser')
        self.assertEqual(classify_page_format(soup, ['VideoObject'], 'https://example.org/videos/lesson', 'text/html'), 'video')

    def test_regular_article_is_webpage(self):
        from bs4 import BeautifulSoup
        from resource_discovery.search import classify_page_format
        soup = BeautifulSoup('<article><video src="clip.mp4"></video></article>', 'html.parser')
        self.assertEqual(classify_page_format(soup, ['Article'], 'https://example.org/story', 'text/html'), 'webpage')

    def test_pdf_format(self):
        from resource_discovery.search import classify_page_format
        self.assertEqual(classify_page_format(None, [], 'https://example.org/guide.pdf', 'application/pdf'), 'document')

    def test_difficulty_is_explicit(self):
        from resource_discovery.resource_classifier import classify_difficulty
        self.assertEqual(classify_difficulty('Python for Beginners'), 'Beginner')
        self.assertIsNone(classify_difficulty('Learn Python'))
        self.assertIsNone(classify_difficulty('Beginner to Advanced'))

    def test_structured_pricing(self):
        from resource_discovery.resource_classifier import classify_structured_pricing
        self.assertEqual(classify_structured_pricing([{'offers': {'price': '0'}}]), 'free')
        self.assertIsNone(classify_structured_pricing([{'offers': {'price': '15'}}]))
        self.assertIsNone(classify_structured_pricing([{}]))

    def test_normalized_difficulty(self):
        from resource_discovery.resource_normalizer import create_resource
        result = create_resource('Python', 'https://example.org', difficulty='Beginner')
        self.assertEqual(result['difficulty'], 'Beginner')


class PrimaryVideoRegressionTests(unittest.TestCase):
    def test_article_with_videoobject_remains_webpage(self):
        from bs4 import BeautifulSoup
        from resource_discovery.search import classify_page_format
        soup = BeautifulSoup('<meta property="og:type" content="article">', 'html.parser')
        self.assertEqual(classify_page_format(
            soup, ['Article', 'VideoObject'],
            'https://www.geeksforgeeks.org/python/python-programming-language-tutorial/',
            'text/html'), 'webpage')

    def test_videoobject_on_generic_tutorial_is_not_enough(self):
        from bs4 import BeautifulSoup
        from resource_discovery.search import classify_page_format
        soup = BeautifulSoup('<div>Text tutorial with embedded video</div>', 'html.parser')
        self.assertEqual(classify_page_format(
            soup, ['VideoObject'], 'https://example.org/python-tutorial',
            'text/html'), 'webpage')

    def test_explicit_video_og_type(self):
        from bs4 import BeautifulSoup
        from resource_discovery.search import classify_page_format
        soup = BeautifulSoup('<meta property="og:type" content="video.other">', 'html.parser')
        self.assertEqual(classify_page_format(
            soup, [], 'https://example.org/lesson', 'text/html'), 'video')

    @patch('resource_discovery.search.search_brave')
    @patch('resource_discovery.search.inspect_resource')
    def test_video_only_search_targets_video_and_still_filters(self, inspect, brave):
        brave.return_value = [{'url': 'https://example.org/article'},
                              {'url': 'https://example.org/video'}]
        inspect.side_effect = [
            {'resource_format': 'webpage'}, {'resource_format': 'video'},
        ]
        results = search_resources('Python programming tutorial',
                                   {'formats': ['video']})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['resource_format'], 'video')
        self.assertIn('video', brave.call_args.args[0].lower())

    @patch('resource_discovery.search.search_brave', return_value=[])
    def test_unfiltered_query_is_not_modified(self, brave):
        search_resources('Python programming tutorial')
        self.assertEqual(brave.call_args.args[0], 'Python programming tutorial')


class YouTubeMetadataRegressionTests(unittest.TestCase):
    def test_full_course_classification(self):
        from resource_discovery.resource_classifier import classify_youtube_resource_type
        self.assertEqual(classify_youtube_resource_type("Python Full Course for Beginners"), "course")
        self.assertEqual(classify_youtube_resource_type("Complete Python Tutorial"), "course")

    def test_ambiguous_video_stays_unclassified(self):
        from resource_discovery.resource_classifier import classify_youtube_resource_type
        self.assertIsNone(classify_youtube_resource_type("How Python Works"))
        self.assertIsNone(classify_youtube_resource_type("Learn Python in 5 Minutes"))

    def test_youtube_player_description(self):
        import json
        from bs4 import BeautifulSoup
        from resource_discovery.youtube_parser import extract_youtube_metadata
        player = {"videoDetails": {"author": "Instructor", "shortDescription": "Specific Python lesson", "lengthSeconds": "120"}}
        soup = BeautifulSoup('<script>var ytInitialPlayerResponse = ' + json.dumps(player) + ';</script>', 'html.parser')
        metadata = extract_youtube_metadata(soup)
        self.assertEqual(metadata["description"], "Specific Python lesson")
        self.assertEqual(metadata["duration_seconds"], 120)

    @patch('resource_discovery.search.requests.get')
    def test_inspection_prefers_video_description(self, get):
        import json
        from resource_discovery.search import inspect_resource
        player = {"videoDetails": {"shortDescription": "Actual lesson summary", "author": "Teacher"}}
        html = ('<html><head><meta property="og:title" content="Python Full Course">'
                '<meta property="og:description" content="Generic YouTube summary"></head>'
                '<body><script>var ytInitialPlayerResponse = ' + json.dumps(player) + ';</script></body></html>')
        response = get.return_value
        response.headers = {"Content-Type": "text/html"}
        response.content = html.encode()
        response.raise_for_status.return_value = None
        result = inspect_resource({"url": "https://www.youtube.com/watch?v=abc123", "title": "Python Full Course"})
        self.assertEqual(result["description"], "Actual lesson summary")
        self.assertEqual(result["resource_type"], "course")

    def test_youtube_difficulty(self):
        from resource_discovery.resource_classifier import classify_difficulty
        self.assertEqual(classify_difficulty("Python for Beginners", "Intro to Python"), "Beginner")
        self.assertIsNone(classify_difficulty("Python", "Beginner through advanced"))


class MetadataQualityRegressionTests(unittest.TestCase):
    def test_html_entities_and_markup_cleaned(self):
        from resource_discovery.resource_normalizer import create_resource
        result = create_resource("Example", "https://example.org", description="It&amp;#x27;s &quot;great&quot; <strong>tutorial</strong>.")
        self.assertEqual(result["description"], "It's \"great\" tutorial.")

    def test_standard_entities_cleaned(self):
        from resource_discovery.resource_normalizer import create_resource
        result = create_resource("Example", "https://example.org", description="It&#x27;s &quot;great&quot; <strong>tutorial</strong>.")
        self.assertEqual(result["description"], "It's \"great\" tutorial.")

    def test_free_interactive_tutorial(self):
        from resource_discovery.resource_classifier import classify_pricing_model
        self.assertEqual(classify_pricing_model(title="Learn Python - Free Interactive Python Tutorial", page_text="Subscribe monthly to other courses"), "free")

    def test_sitewide_subscription_not_resource_price(self):
        from resource_discovery.resource_classifier import classify_pricing_model
        self.assertIsNone(classify_pricing_model(title="Python Tutorial", description="Learn Python step by step", page_text="Become a member. Monthly subscription required for premium plans."))

    def test_explicit_subscription_still_detected(self):
        from resource_discovery.resource_classifier import classify_pricing_model
        self.assertEqual(classify_pricing_model(title="Python course", description="Subscription required to access this course"), "subscription")


class FilterStage1RegressionTests(unittest.TestCase):
    def test_all_filter_only_groups_initiate_brave(self):
        values = {"prices": "free", "sources": "YouTube", "resource_types": "course",
                  "formats": "video", "difficulties": "Beginner"}
        for group, value in values.items():
            with self.subTest(group=group), patch('resource_discovery.search.search_brave', return_value=[]) as brave:
                search_resources('', {group: [value]})
                brave.assert_called_once()
                self.assertTrue(brave.call_args.args[0])

    def test_no_query_no_filters_does_not_search(self):
        with patch('resource_discovery.search.search_brave') as brave:
            self.assertEqual(search_resources('', {}), [])
            brave.assert_not_called()

    def test_youtube_source_aliases(self):
        filters = normalize_filters({'sources': ['YouTube']})
        for name in ('YouTube', 'youtube.com', 'www.youtube.com', 'm.youtube.com'):
            with self.subTest(name=name):
                self.assertTrue(matches_discovery_filters({'source': name}, filters))
        self.assertFalse(matches_discovery_filters({'source': 'notyoutube.com'}, filters))

    def test_source_or_and_cross_group_and(self):
        filters = normalize_filters({'sources': ['YouTube', 'example.org'], 'formats': ['video']})
        self.assertTrue(matches_discovery_filters({'source': 'youtube.com', 'resource_format': 'video'}, filters))
        self.assertTrue(matches_discovery_filters({'source': 'www.example.org', 'resource_format': 'video'}, filters))
        self.assertFalse(matches_discovery_filters({'source': 'youtube.com', 'resource_format': 'webpage'}, filters))

    def test_multiple_sources_not_conjoined_in_query(self):
        from resource_discovery.discovery_filters import build_discovery_query
        query = build_discovery_query('', {'sources': ['YouTube', 'example.org']})
        self.assertNotIn('site:', query)

    def test_explicit_query_unchanged_for_source_filter(self):
        from resource_discovery.discovery_filters import build_discovery_query
        self.assertEqual(build_discovery_query('Python', {'sources': ['YouTube']}), 'Python')


class YouTubePricingRegressionTests(unittest.TestCase):
    def _metadata(self, player):
        import json
        from bs4 import BeautifulSoup
        from resource_discovery.youtube_parser import extract_youtube_metadata
        soup = BeautifulSoup(
            '<script>var ytInitialPlayerResponse = ' + json.dumps(player) + ';</script>',
            'html.parser',
        )
        return extract_youtube_metadata(soup)

    def test_public_playable_stream_is_free(self):
        metadata = self._metadata({
            'playabilityStatus': {'status': 'OK'},
            'streamingData': {'adaptiveFormats': [{'itag': 140}]},
            'videoDetails': {'shortDescription': 'Paid courses advertised elsewhere'},
        })
        self.assertEqual(metadata['pricing_model'], 'free')

    def test_restricted_video_not_assumed_free(self):
        metadata = self._metadata({
            'playabilityStatus': {'status': 'LOGIN_REQUIRED'},
            'streamingData': {'formats': [{'itag': 18}]},
        })
        self.assertIsNone(metadata['pricing_model'])

    def test_unavailable_video_not_assumed_free(self):
        metadata = self._metadata({'playabilityStatus': {'status': 'UNPLAYABLE'}})
        self.assertIsNone(metadata['pricing_model'])

    def test_missing_player_evidence_not_assumed_free(self):
        self.assertIsNone(self._metadata({'videoDetails': {'title': 'Python'}})['pricing_model'])
        self.assertIsNone(self._metadata({'playabilityStatus': {'status': 'OK'}})['pricing_model'])

    @patch('resource_discovery.search.requests.get')
    def test_inspected_public_video_matches_video_and_free(self, get):
        import json
        from resource_discovery.search import inspect_resource
        player = {
            'playabilityStatus': {'status': 'OK'},
            'streamingData': {'formats': [{'itag': 18}]},
            'videoDetails': {'shortDescription': 'Python lesson', 'author': 'Teacher'},
        }
        html = ('<html><head><meta property="og:title" content="Python lesson"></head>'
                '<body><script>var ytInitialPlayerResponse = ' + json.dumps(player)
                + ';</script></body></html>')
        response = get.return_value
        response.headers = {'Content-Type': 'text/html'}
        response.content = html.encode()
        response.raise_for_status.return_value = None
        resource = inspect_resource({'url': 'https://www.youtube.com/watch?v=abc123', 'title': 'Python lesson'})
        self.assertEqual(resource['pricing_model'], 'free')
        self.assertTrue(matches_discovery_filters(resource, normalize_filters(
            {'formats': ['video'], 'prices': ['free']})))


class QueryRelevanceRegressionTests(unittest.TestCase):
    def test_multiple_skills_are_alternatives(self):
        from resource_discovery.discovery_filters import build_discovery_query
        self.assertEqual(build_discovery_query('tutorial', {'skills': ['Python', 'JavaScript']}),
                         'tutorial (Python OR JavaScript)')

    def test_multiword_degree_programs_are_quoted_alternatives(self):
        from resource_discovery.discovery_filters import build_discovery_query
        self.assertEqual(build_discovery_query('', {'degree_programs': ['Computer Science', 'Data Science']}),
                         '("Computer Science" OR "Data Science") learning resources')

    def test_multiple_careers_are_alternatives(self):
        from resource_discovery.discovery_filters import build_discovery_query
        self.assertEqual(build_discovery_query('tutorial', {'career_fields': ['Data Analyst', 'Software Development']}),
                         'tutorial ("Data Analyst" OR "Software Development") skills')

    def test_no_intent_keeps_unfiltered_query(self):
        from resource_discovery.discovery_filters import build_discovery_query
        self.assertEqual(build_discovery_query('Python programming tutorial'), 'Python programming tutorial')

    def test_concrete_filters_do_not_conjoin_multiple_values(self):
        from resource_discovery.discovery_filters import build_discovery_query
        query = build_discovery_query('', {'sources': ['YouTube', 'example.org'], 'prices': ['free', 'subscription']})
        self.assertNotIn('site:', query)
        self.assertNotIn('subscription', query)
        self.assertTrue(query)


class FreeAndUnverifiedPricingTests(unittest.TestCase):
    def test_free_accepts_unknown_and_confirmed_free(self):
        filters = normalize_filters({'prices': ['free']})
        self.assertTrue(matches_discovery_filters({'pricing_model': None}, filters))
        self.assertTrue(matches_discovery_filters({'pricing_model': 'free'}, filters))

    def test_free_rejects_known_paid_pricing(self):
        filters = normalize_filters({'prices': ['free']})
        for value in ('paid', 'subscription', 'one-time'):
            with self.subTest(value=value):
                self.assertFalse(matches_discovery_filters({'pricing_model': value}, filters))

    def test_video_and_free_preserve_format_requirement(self):
        filters = normalize_filters({'formats': ['video'], 'prices': ['free']})
        self.assertTrue(matches_discovery_filters({'resource_format': 'video', 'pricing_model': None}, filters))
        self.assertFalse(matches_discovery_filters({'resource_format': 'webpage', 'pricing_model': None}, filters))

    def test_other_pricing_selections_remain_strict(self):
        filters = normalize_filters({'prices': ['subscription']})
        self.assertFalse(matches_discovery_filters({'pricing_model': None}, filters))
        self.assertTrue(matches_discovery_filters({'pricing_model': 'subscription'}, filters))

    @patch('resource_discovery.search.search_brave')
    @patch('resource_discovery.search.inspect_resource')
    def test_confirmed_free_sorted_first_with_stable_relevance(self, inspect, brave):
        brave.return_value = [{'url': f'https://example.org/{i}'} for i in range(5)]
        inspected = [
            {'url': 'a', 'pricing_model': None},
            {'url': 'b', 'pricing_model': 'free'},
            {'url': 'c', 'pricing_model': 'subscription'},
            {'url': 'd', 'pricing_model': None},
            {'url': 'e', 'pricing_model': 'free'},
        ]
        inspect.side_effect = inspected
        results = search_resources('tutorial', {'prices': ['free']})
        self.assertEqual([r['url'] for r in results], ['b', 'e', 'a', 'd'])

    def test_unfiltered_unknown_still_accepted(self):
        self.assertTrue(matches_discovery_filters({'pricing_model': None}, normalize_filters({})))
