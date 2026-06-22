from acoupi.system.constants import CeleryConfig


def test_celery_config_defaults_include_short_beat_loop_interval():
    config = CeleryConfig().model_dump()

    assert config["beat_max_loop_interval"] == 1
