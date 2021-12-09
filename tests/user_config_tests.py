from unittest.mock import Mock

import pytest

import telegram_bot


MOCKED_USER_CONFIG_PATH = 'tests/mock_config.yml'


@pytest.fixture(autouse=True)
def mock_config_path(monkeypatch):
    monkeypatch.setattr(telegram_bot, 'USER_CONFIG_PATH', MOCKED_USER_CONFIG_PATH)


class TestUserConfigHandling:
    def test_get_subscribed_users(self):
        res = telegram_bot.get_subscribed_users()
        assert len(res) == 1
        assert res.get('christian') is not None
        assert res.get('christian').get(telegram_bot.UserConfig.is_subscribed.value) is True
        assert res.get('christian').get(telegram_bot.UserConfig.last_cite_count.value) == 2

    def test_add_new_user_to_config(self):
        telegram_bot.add_new_user_to_config('maja')
        res = telegram_bot.get_subscribed_users()
        assert len(res) == 2
        assert res.get('maja') is not None
        assert res.get('maja').get(telegram_bot.UserConfig.is_subscribed.value) is True
        assert res.get('maja').get(telegram_bot.UserConfig.last_cite_count.value) == 0

