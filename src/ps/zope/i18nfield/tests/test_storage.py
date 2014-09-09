# -*- coding: utf-8 -*-
"""Integration tests for the i18n utility methods."""

# python imports
try:
    import unittest2 as unittest
except ImportError:
    import unittest

# zope imports
from zope.component import provideUtility
from zope.globalrequest import setRequest
from zope.interface import implementer

# local imports
from ps.zope.i18nfield import (
    interfaces,
    storage,
)


@implementer(interfaces.ILanguageAvailability)
class LanguageAvailability(object):

    def getDefaultLanguage(self, combined=False):
        return u'en'

    def getAvailableLanguages(self, combined=False):
        return [u'de', u'en', u'es', u'fr', u'pt']

    def getLanguages(self, combined=False):
        pass

    def getLanguageListing(self, combined=False):
        pass


class TestI18NDict(unittest.TestCase):
    """Test case for the I18n language dictionary."""

    def setUp(self):
        super(TestI18NDict, self).setUp()
        provideUtility(LanguageAvailability())

    def test_standard(self):
        """Test that the dictionary access with no default language."""
        data = storage.I18NDict()
        self.assertIsNone(data.get(u'en'))
        data[u'en'] = u'English'
        self.assertEqual(data.get(u'en'), u'English')
        data[u'es'] = u'Español'
        self.assertEqual(data.get(u'es'), u'Español')
        self.assertEqual(len(data.keys()), 2)

    def test_default(self):
        """Test the default value method with a default language set."""
        data = storage.I18NDict()
        data.default_language = u'es'

        # no values - fallback is None
        self.assertIsNone(data.get_default_value())

        # one value - fallback is the first value found
        data[u'fr'] = u'French'
        self.assertEqual(data.get_default_value(), u'French')

        # two values - fallback comes from global default (ILanguageSettings)
        data[u'en'] = u'English'
        self.assertEqual(data.get_default_value(), u'English')

        # three values - fallback comes from I18nDict default language
        data[u'es'] = u'Español'
        self.assertEqual(data.get_default_value(), u'Español')

        # set to non-existent default language - default from ILanguageSettings
        data.default_language = u'de'
        self.assertEqual(data.get_default_value(), u'English')

        # default comes from global registry
        # self.assertEqual(data.get_default_value(), u'French')

        # default comes from I18nDict internally saved default language
        data.default_language = u'en'
        self.assertEqual(data.get_default_value(), u'English')

    def test_no_default(self):
        """Test the default value method with no default langauge set."""
        data = storage.I18NDict()

        # no values - default is None
        self.assertIsNone(data.get_default_value())

        # one value - fallback is first value found
        data[u'fr'] = u'French'
        self.assertEqual(data.get_default_value(), u'French')

        # two values - global registry default is used
        data[u'en'] = u'English'
        self.assertEqual(data.get_default_value(), u'English')

        # three values - global registry default is still used
        data[u'es'] = u'Español'
        self.assertEqual(data.get_default_value(), u'English')

    def test_unicode_representation(self):
        """Test the __unicode__ method of the dictionary."""
        setRequest(None)
        data = storage.I18NDict()
        data.required = True

        # no request, no values
        self.assertEqual(unicode(data), u'None')

        # no request - fallback to first value
        data[u'fr'] = u'French'
        self.assertEqual(unicode(data), u'French')

        # no request - fallback to global default (English)
        data[u'en'] = u'English'
        data[u'es'] = u'Español'
        self.assertEqual(unicode(data), u'English')

    def test_string_representation(self):
        """Test the __str__ method of the dictionary."""
        setRequest(None)
        data = storage.I18NDict()
        data.default_language = u'es'
        data.required = True

        # no request, no values
        self.assertEqual(str(data), 'None')

        # no request - fallback to first value
        data[u'fr'] = u'French'
        self.assertEqual(str(data), 'French')

    def test_not_required(self):
        """Test the __unicode__ method without a required field."""
        setRequest(None)
        data = storage.I18NDict()
        data.default_language = u'es'
        data.required = False
        data[u'fr'] = u'French'
        data[u'de'] = u'German'
        data[u'es'] = u'Español'

        # no request, no value for default language 'en'
        self.assertEqual(unicode(data), u'None')

        # with required
        data.required = True
        self.assertEqual(unicode(data), u'Español')

    def test_from_text(self):
        """Test the from_text method."""
        data = storage.I18NDict.from_text(u'Test value')
        self.assertEqual(data, {u'__default_value': u'Test value'})
        self.assertEqual(unicode(data), u'Test value')

    def test_to_dict(self):
        original = storage.I18NDict()
        original[u'en'] = u'English'
        original[u'es'] = u'Español'
        self.assertEqual(len(original), 2)
        copy = original.to_dict()
        self.assertEqual(len(copy), 2)
        self.assertIn(u'en', copy.keys())
        self.assertIn(u'Español', copy.values())

    def test_copy(self):
        original = storage.I18NDict()
        original.default_language = u'es'
        original.required = True
        original[u'en'] = u'English'
        original[u'es'] = u'Español'
        self.assertEqual(len(original), 2)
        copy = original.copy()
        self.assertEqual(len(copy), 2)
        self.assertIn(u'es', copy.keys())
        self.assertIn(u'English', copy.values())
        self.assertEqual(copy.default_language, original.default_language)
        self.assertEqual(copy.required, original.required)

    def test_set_item(self):
        """Test the checks from __setitem__ method."""
        data = storage.I18NDict()
        data[u'fr'] = u'French'
        self.assertIn(u'fr', data)
        data[u'__default_value'] = u'Default value'
        self.assertIn(u'Default value', data.values())
        data[u'non-existent'] = u'Invalid'
        self.assertEqual(len(data), 2)
        data[u'en'] = u''
        self.assertEqual(len(data), 2)
        self.assertNotIn(u'en', data)

    def test_update(self):
        """Test the update method."""
        data = storage.I18NDict({u'en': u'English', u'invalid': u'blah'})
        self.assertEqual(len(data), 1)
        self.assertIn(u'en', data)

        data.update({
            u'es': u'Español',
            u'fr': u'François',
            u'fake': u'Non-value',
        })
        self.assertEqual(len(data), 3)
        self.assertIn(u'Español', data.values())
        self.assertIn(u'François', data.values())

        data.update([
            (u'de', u'Deutsch'),
            (u'pt', u'Português'),
            (u'slang', u'Jibber jabber'),
        ])
        self.assertEqual(len(data), 5)
        self.assertIn(u'de', data.keys())
        self.assertIn(u'pt', data.keys())

    def test_add(self):
        """Test the add method."""
        data = storage.I18NDict()
        data.add(u'de', u'Deutsch')
        self.assertEqual(len(data), 1)
        self.assertIn(u'de', data)
        data.add(u'fake', u'Fake language')
        self.assertEqual(len(data), 1)

    def test_remove(self):
        """Test the remove method."""
        data = storage.I18NDict({u'en': u'English', u'de': u'Deutsch'})
        self.assertEqual(len(data), 2)
        data.remove(u'de')
        self.assertEqual(len(data), 1)
        self.assertNotIn(u'de', data)
        data.remove(u'not')
        self.assertEqual(len(data), 1)