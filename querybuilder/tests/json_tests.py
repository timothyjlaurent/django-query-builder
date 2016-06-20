import unittest
from django.test.testcases import TestCase
from django.test.utils import override_settings
from querybuilder.fields import JsonField
from querybuilder.query import Query, JsonQueryset
from querybuilder.tests.models import MetricRecord
from querybuilder.tests.utils import get_postgres_version


@override_settings(DEBUG=True)
class JsonFieldTest(TestCase):

    def test_one(self):
        if get_postgres_version() < (9, 4):
            raise unittest.SkipTest('Invalid Postgres version for test')

        metric_record = MetricRecord(data={
            'one': 1,
            'two': 'two',
        })
        metric_record.save()

        one_field = JsonField('data', key='one', alias='my_one_alias')
        two_field = JsonField('data', key='two', alias='my_two_alias')

        query = Query().from_table(MetricRecord, fields=[two_field]).where(**{
            two_field.get_where_key(): 'one'
        })
        self.assertEqual(
            query.get_sql(),
            (
                'SELECT tests_metricrecord.data->\'two\' AS my_two_alias FROM tests_metricrecord '
                'WHERE (tests_metricrecord.data->>\'two\' = %(A0)s)'
            )
        )
        self.assertEqual(query.select(), [])

        query = Query().from_table(MetricRecord, fields=[two_field]).where(**{
            two_field.get_where_key(): 'two'
        })
        self.assertEqual(
            query.get_sql(),
            (
                'SELECT tests_metricrecord.data->\'two\' AS my_two_alias FROM tests_metricrecord '
                'WHERE (tests_metricrecord.data->>\'two\' = %(A0)s)'
            )
        )
        self.assertEqual(query.select(), [{'my_two_alias': 'two'}])

        query = Query().from_table(MetricRecord, fields=[one_field]).where(**{
            one_field.get_where_key(): '1'
        })
        self.assertEqual(
            query.get_sql(),
            (
                'SELECT tests_metricrecord.data->\'one\' AS my_one_alias FROM tests_metricrecord '
                'WHERE (tests_metricrecord.data->>\'one\' = %(A0)s)'
            )
        )
        self.assertEqual(query.select(), [{'my_one_alias': 1}])

        query = Query().from_table(MetricRecord, fields=[one_field]).where(**{
            one_field.get_where_key(): '2'
        })
        self.assertEqual(
            query.get_sql(),
            (
                'SELECT tests_metricrecord.data->\'one\' AS my_one_alias FROM tests_metricrecord '
                'WHERE (tests_metricrecord.data->>\'one\' = %(A0)s)'
            )
        )
        self.assertEqual(query.select(), [])


@override_settings(DEBUG=True)
class JsonQuerysetTest(TestCase):

    def test_one(self):
        if get_postgres_version() < (9, 4):
            raise unittest.SkipTest('Invalid Postgres version for test')

        metric_record = MetricRecord(data={
            'one': 1,
            'two': 'two',
        })
        metric_record.save()

        metric_record2 = MetricRecord(data={
            'one': 5,
        })
        metric_record2.save()

        record = JsonQueryset(model=MetricRecord).filter(**{'data->two': 'one'}).first()
        self.assertIsNone(record)

        record = JsonQueryset(model=MetricRecord).filter(**{'data->two': 'two'}).first()
        self.assertEqual(record.data['two'], 'two')

        record = JsonQueryset(model=MetricRecord).filter(**{'data->one': '1'}).first()
        self.assertEqual(record.data['one'], 1)

        record = JsonQueryset(model=MetricRecord).filter(**{'data->one': '2'}).first()
        self.assertIsNone(record)

        records = list(JsonQueryset(model=MetricRecord).order_by('data->one'))
        self.assertEqual(records[0].data['one'], 1)
        self.assertEqual(records[1].data['one'], 5)
