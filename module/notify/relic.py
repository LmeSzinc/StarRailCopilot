from datetime import datetime

# Require the last inventory update to reach 99% of the observed capacity.
RELIC_NEAR_FULL_PERCENT = 99

MESSAGES = {
    'zh-CN': (
        '遗器已满',
        '遗器数量：{value}/{total}（已重新读取并确认）\n'
        '上次更新：{previous}/{total}\n读取时间：{time}（SRC 主机时间）\n'
        '请手动清理遗器背包。SRC 不会自动分解遗器。',
    ),
    'zh-TW': (
        '遺器已滿',
        '遺器數量：{value}/{total}（已重新讀取並確認）\n'
        '上次更新：{previous}/{total}\n讀取時間：{time}（SRC 主機時間）\n'
        '請手動清理遺器背包。SRC 不會自動分解遺器。',
    ),
    'en-US': (
        'Relic inventory full',
        'Relics: {value}/{total} (read again and confirmed)\n'
        'Previous update: {previous}/{total}\nRead at: {time} (SRC host time)\n'
        'Please clear your relic inventory manually. SRC will not salvage relics automatically.',
    ),
    'ja-JP': (
        '遺物の所持数が上限に達しました',
        '遺物数：{value}/{total}（再読み取りで確認済み）\n'
        '前回の更新：{previous}/{total}\n確認時刻：{time}（SRC ホスト時刻）\n'
        '遺物を手動で整理してください。SRC は遺物を自動分解しません。',
    ),
    'es-ES': (
        'Inventario de artefactos lleno',
        'Artefactos: {value}/{total} (confirmado con una nueva lectura)\n'
        'Actualización anterior: {previous}/{total}\nLectura: {time} (hora del servidor SRC)\n'
        'Libera espacio manualmente. SRC no desguazará artefactos automáticamente.',
    ),
}


def near_full(value, total, time):
    try:
        measured = time if isinstance(time, datetime) else datetime.fromisoformat(time)
    except (ValueError, TypeError):
        return False
    return (type(value) is int and type(total) is int and total > 0
            and 0 <= value <= total and value * 100 >= total * RELIC_NEAR_FULL_PERCENT
            and measured.year > 2020)


def notification_language():
    # Read the saved GUI preference, including changes made while the scheduler runs.
    from deploy.Windows.utils import DEPLOY_CONFIG, poor_yaml_read
    language = poor_yaml_read(DEPLOY_CONFIG).get('Language', 'en-US')
    return next((key for key in MESSAGES if key.lower() == str(language).lower()), 'en-US')


def relic_notice(value, total, time, previous, lang='en-US'):
    title, content = MESSAGES.get(lang, MESSAGES['en-US'])
    return title, content.format(value=value, total=total, time=time, previous=previous)
