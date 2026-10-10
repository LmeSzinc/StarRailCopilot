from module.device.cloud import backend
from module.exception import RequestHumanTakeover


def create_device(config):
    from module.config.config import AzurLaneConfig

    if isinstance(config, str):
        config = AzurLaneConfig(config)
    if config.is_cloud_direct:
        if backend is None:
            raise RequestHumanTakeover('当前设备后端不受支持。')
        return backend.create_device(config)
    from module.device.device import Device
    return Device(config=config)
