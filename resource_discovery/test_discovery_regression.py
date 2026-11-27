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
        self.assertFalse(matches_discovery_filters({'resource_format': 'video', 'pricing_model': None}, filters))
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
