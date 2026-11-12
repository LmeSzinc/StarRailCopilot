import json
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from requests import Response

import module.alas as alas
import module.config.stored.classes as stored_classes
import module.exception as exceptions
import module.notify.notify as notify
import module.notify.relic as relic
import tasks.item.data_update as data_update


class RelicNotificationTest(unittest.TestCase):
    def test_telegram_acceptance_and_rejection(self):
        for status, payload, expected in [
            (200, {'ok': True, 'result': {'message_id': 123}}, True),
            (200, {'ok': False, 'error_code': 400}, False),
            (403, {'ok': False, 'error_code': 403}, False),
            (200, {}, False),
        ]:
            with self.subTest(status=status, payload=payload):
                response = Response()
                response.status_code = status
                response._content = json.dumps(payload).encode()
                notifier = Mock(params={'required': []})
                notifier.notify.return_value = response
                with patch.object(notify, 'get_notifier', return_value=notifier):
                    self.assertIs(notify.handle_notify('provider: telegram'), expected)

    def test_telegram_invalid_response(self):
        for response in [None, True, Response()]:
            notifier = Mock(params={'required': []})
            notifier.notify.return_value = response
            with patch.object(notify, 'get_notifier', return_value=notifier):
                self.assertFalse(notify.handle_notify('provider: telegram'))

    def test_threshold_is_99_percent_of_actual_capacity(self):
        for value, total, expected in [(2969, 3000, False), (2970, 3000, True),
                                       (3959, 4000, False), (3960, 4000, True),
                                       (4949, 5000, False), (4950, 5000, True),
                                       (0, 0, False), (4001, 4000, False)]:
            with self.subTest(value=value, total=total):
                self.assertEqual(relic.near_full(value, total, '2026-10-11 12:00:00'), expected)
        self.assertFalse(relic.near_full(3000, 3000, '2020-01-01 00:00:00'))
        self.assertFalse(relic.near_full(3000, 3000, 'bad timestamp'))

    def test_all_gui_languages_and_fallback(self):
        for lang in ['zh-CN', 'zh-TW', 'en-US', 'ja-JP', 'es-ES']:
            title, content = relic.relic_notice(4000, 4000, '2026-10-11 12:00:00', 3960, lang)
            self.assertTrue(title)
            self.assertIn('4000/4000', content)
            self.assertIn('3960/4000', content)
            self.assertNotIn('{', content)
        self.assertEqual(relic.relic_notice(4000, 4000, 'now', 3960, 'unknown')[0],
                         'Relic inventory full')
        with patch('deploy.Windows.utils.poor_yaml_read', return_value={'Language': 'zh-TW'}):
            self.assertEqual(relic.notification_language(), 'zh-TW')

    def test_dynamic_capacity_is_saved(self):
        obj = stored_classes.StoredRelic('Dungeon.DungeonStorage.Relic')
        config = Mock(data={}, modified={}, auto_update=False)
        config.multi_set.return_value = nullcontext()
        obj._bind(config)
        obj.set(3999, 4000)
        self.assertEqual((obj.value, obj.total), (3999, 4000))

    def test_inventory_ocr_requires_two_matching_fresh_frames(self):
        cases = [([(2615, 385, 3000)] * 2, (2615, 3000)),
                 ([(4000, 0, 4000)] * 2, (4000, 4000)),
                 ([(5000, 0, 5000)] * 2, (5000, 5000)),
                 ([(3000, 0, 3000)], None),
                 ([(3000, 0, 3000), (2615, 385, 3000)], None),
                 ([(-1, 3001, 3000)] * 2, None),
                 ([(3100, -100, 3000)] * 2, None),
                 ([(0, 0, 0)] * 2, None)]
        for readings, expected in cases:
            with self.subTest(readings=readings):
                obj = Mock()
                obj.loop.return_value = iter([None] * len(readings))
                with patch.object(data_update, 'RelicOcr') as ocr, patch.object(data_update, 'Timer') as timer:
                    ocr.return_value.ocr_single_line.side_effect = readings
                    timer.return_value.start.return_value.reached.return_value = False
                    self.assertEqual(data_update.DataUpdate._get_relic(obj), expected)
                    obj.loop.assert_called_once_with(skip_first=False)

    def test_notification_requires_prior_near_full_and_confirmed_same_capacity(self):
        for previous, current, expected in [
            ((2969, 3000), (3000, 3000), False),
            ((2970, 3000), (3000, 3000), True),
            ((2970, 3000), (2999, 3000), False),
            ((3000, 3000), (4000, 4000), False),
            ((3960, 4000), (4000, 4000), True),
            ((4000, 4000), None, False),
        ]:
            with self.subTest(previous=previous, current=current):
                obj = Mock()
                obj.config.stored.Relic.time = '2026-10-11 12:01:00'
                with patch('module.notify.handle_notify', return_value=True) as send, \
                        patch.object(relic, 'notification_language', return_value='zh-CN'):
                    result = data_update.DataUpdate._notify_relic_full(
                        obj, (*previous, '2026-10-11 12:00:00'), current)
                    self.assertEqual(result, expected)
                    self.assertEqual(send.call_count, int(expected))

    def test_entry_failure_below_threshold_does_not_navigate_or_send(self):
        obj = Mock()
        obj.config.stored.Relic = SimpleNamespace(value=2615, total=3000, time='2026-10-11 12:00:00')
        self.assertFalse(data_update.DataUpdate.check_relic_full(obj))
        obj.ui_ensure.assert_not_called()
        obj._notify_relic_full.assert_not_called()

    def test_near_full_entry_failure_rechecks_inventory(self):
        obj = Mock()
        obj.config.stored.Relic.value = 3960
        obj.config.stored.Relic.total = 4000
        obj.config.stored.Relic.time = '2026-10-11 12:00:00'
        obj._get_relic.return_value = (4000, 4000)
        data_update.DataUpdate.check_relic_full(obj)
        obj._get_relic.assert_called_once()
        obj.config.stored.Relic.set.assert_called_once_with(4000, 4000)
        obj._notify_relic_full.assert_called_once_with((3960, 4000, '2026-10-11 12:00:00'), (4000, 4000))

    def test_failed_entry_stops_without_generic_push(self):
        obj = Mock()
        obj.command = Mock(side_effect=exceptions.DungeonEntryFailed)
        with patch.object(alas, 'handle_notify') as send:
            with self.assertRaises(SystemExit):
                alas.AzurLaneAutoScript.run(obj, 'command')
            send.assert_not_called()
            obj.error_postprocess.assert_called_once()


if __name__ == '__main__':
    unittest.main()
