from pathlib import Path

from dev_tools.exchange_code import code_cn, code_global
from module.config.deep import deep_set
from module.config.utils import write_file

if __name__ == '__main__':
    data = {}

    self = code_cn.GameRedeemCode()
    codes = self.get_redeem_codes()
    for code in codes:
        row = {
            "expires_at": self.expires_iso,
        }
        deep_set(data, ['codes', 'CN', code], row)

    self = code_global.GameRedeemCode(proxy='http://127.0.0.1:7890')
    codes = self.get_redeem_codes()
    for code in codes:
        row = {
            "expires_at": self.expires_iso,
        }
        deep_set(data, ['codes', 'OVERSEA', code], row)

    # write file
    file = Path(__file__).with_name('codes.json')
    write_file(str(file), data)
