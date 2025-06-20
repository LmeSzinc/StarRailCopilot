import os.path
from datetime import datetime

from module.base.decorator import cached_property
from module.config.deep import deep_get, deep_iter, deep_set
from module.config.server import to_server
from module.config.utils import read_file
from module.logger import logger
from tasks.base.ui import UI


def nowtz():
    """
    Get datatime now with timezone
    """
    return datetime.now().replace(microsecond=0).astimezone()


class CodeManager:
    def __init__(self, main: UI):
        self.main = main

    @cached_property
    def code_current(self):
        """
        Returns:
            dict[dict[str, datatime]]:
                {
                    "CODESTRING": { "expired_at": ...},
                    ...
                }
        """
        package = self.main.config.Emulator_PackageName
        server = to_server(package)
        if server.startswith('CN'):
            path = 'CN'
        elif server.startswith('OVERSEA'):
            path = 'OVERSEA'
        else:
            logger.warning(f'Unknown server from package name: {package}')
            return {}

        file = os.path.abspath('./dev_tools/exchange_code/codes.json')
        codes = read_file(file)
        codes = deep_get(codes, ['codes', path], {})
        now = nowtz()

        data = {}
        for code, row in deep_iter(codes, depth=1):
            code = code[0]
            expires_at = deep_get(row, 'expires_at', '')
            try:
                expires_at = datetime.fromisoformat(expires_at)
            except ValueError:
                logger.warning(f'codes.{path}.expired_at is not a valid time: {expires_at}')
                continue
            if expires_at.tzinfo is None:
                logger.warning(f'codes.{path}.expired_at does not contain tzinfo: {expires_at}')
                continue

            # dropped expired codes
            if expires_at < now:
                # expired, no need to record this code
                continue

            data[code] = {'expires_at': expires_at}

        return data

    @cached_property
    def code_used(self):
        """
        Returns:
            dict[dict[str, datatime]]:
                {
                    "CODESTRING": { "used_at": ...},
                    ...
                }
        """
        current = self.code_current
        # manual data validate
        data = {}
        used = self.main.config.cross_get('Freebies.Freebies.UsedCode', {})
        for code, row in deep_iter(used, depth=1):
            code = code[0]
            used_at = deep_get(row, 'used_at', '')
            try:
                used_at = datetime.fromisoformat(used_at)
            except ValueError:
                logger.warning(f'UsedCode.{code}.used_at is not a valid time: {used_at}')
                continue
            if used_at.tzinfo is None:
                logger.warning(f'UsedCode.{code}.used_at does not contain tzinfo: {used_at}')
                continue

            # remove record if used and expired
            expire = deep_get(current, [code, 'expires_at'])
            if expire is None:
                # old code that has been removed
                logger.info(f'UsedCode.{code} is outdated')
                continue

            data[code] = {'used_at', used_at}

        # save config if dropped any outdated record
        if len(data) != len(used):
            self.main.config.cross_set('Freebies.Freebies.UsedCode', data)

        return data

    def mark_used(self, code):
        # check if it's a known code
        current = self.code_current
        if code not in current:
            return

        now = nowtz().isoformat()
        row = {'used_at': now}
        deep_set(self.code_used, [code], row)

        # save config
        self.main.config.cross_set('Freebies.Freebies.UsedCode', self.code_used)

    def get_codes(self):
        """
        Returns:
            list[str]: List of codes to redeem
        """
        out = []
        for code in self.code_current:
            if code not in self.code_used:
                out.append(code)
        return out

    def check_redeem_code(self):
        """
        Call Freebies task if having redeem code to receive
        """
        # Not enabled
        if not self.main.config.cross_get('Freebies.Freebies.RedemptionCode', False):
            return
        # no codes
        codes = self.get_codes()
        if not codes:
            return

        logger.info(f'Redeem codes available: {codes}')
        self.main.config.task_call('Freebies')
