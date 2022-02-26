import dateutil.parser
import math
import logging
from typing import Tuple, Optional


logger = logging.getLogger(__name__)


def _normalize_last_played(card):
    iso_datetime = card.get('lastModified', None)
    if iso_datetime:
        dt = dateutil.parser.parse(iso_datetime)
        return round(dt.timestamp())


def _normalize_playtime(card):
    """ All known games has 'unit': 'Seconds' in for time fields
    Champions of Anteria is exception, it has 'Hours' for playtime, but uses miliseconds in fact
    That is why we assume Seconds everywhere
    :param card     statistic card with 'format': 'LongTimespan'
    :return         playtime in minutes
    """
    value = card.get('value', None)
    unit = card.get('unit', None)

    if unit == 'Hours':
        factor = 1/60
    elif unit == 'Minutes':
        factor = 1
    elif unit == 'Seconds':
        factor = 60
    elif unit == 'Miliseconds':
        factor = 60000
    else:
        logger.warning(f'Playtime: Unexpected unit [{unit}] with value: [{value}]')
        return None

    if value == "":
        value = 0
    try:
        value = float(value)
    except (ValueError, TypeError):
        return None
    else:
        return value / factor


def _get_playtime_heuristics(time_stats):
    """ Tested on most of UplayClub games
    :param time_stats:     cards with format 'longTimestamp'
    """
    TOTAL_PLAYTIME_DISPLAYNAMES = ['playtime', 'time played', 'play time', 'total play time', 'total playtime']

    cards = []
    if len(time_stats) == 0:
        pass
    elif len(time_stats) == 1:
        cards = [time_stats[0]]
    else:
        for st in time_stats:
            if st['displayName'].lower() in TOTAL_PLAYTIME_DISPLAYNAMES:
                cards = [st]
                break
        else:
            if len(time_stats) == 2:
                # for games with separate time tracking for two game modes
                n1 = time_stats[0]['statName'].lower()
                n2 = time_stats[1]['statName'].lower()
                if (('pvp' in n1 and 'pve' in n2) or ('pve' in n1 and 'pvp' in n2)) or \
                    (('solo' in n1 and 'coop' in n2) or ('coop' in n1 and 'solo' in n2)) or \
                    (('single' in n1 and 'multi' in n2) or ('multi' in n1 and 'single' in n2)):
                    cards = time_stats
        if len(cards) == 0:
            # guessing with indexing based on keywords
            for st in time_stats:
                st['_weight'] = 0
                for sup in ['all', 'total', 'absolute']:
                    if sup in st['displayName'].lower() or sup in st['statName'].lower():
                        st['_weight'] += 1
            time_stats_sorted = sorted(time_stats, key=lambda x: x['_weight'], reverse=True)
            max_weight = time_stats_sorted[0]['_weight']
            for st in time_stats_sorted:
                if st['_weight'] == max_weight:
                    cards.append(st)
                else:  # only less probable cards left
                    break
    time_sum = None
    for card in cards:  # in most cases there is one card
        card_time = _normalize_playtime(card)
        if card_time is not None:
            time_sum = card_time if time_sum is None else card_time + time_sum

    if type(time_sum) == float:
        time_sum = math.floor(time_sum)

    return time_sum


def find_times(statscards: dict, game_id: str = None) -> Tuple[Optional[int], Optional[int]]:
    """
    result[0] - total_playtime in minutes
    result[1] - last_played as timestamp
    """

    # hardcoded fix for buggy time in Champions of Anteria
    if game_id == '4b20d5ee-461e-4d27-8c56-e258577c5ed3':
        for card in statscards:
            if card['statName'] == "TotalDuration" and card['unit'] == 'Hours':
                card['unit'] = 'Miliseconds'
                break

    playtime = None
    last_played = None

    time_stats = []
    for card in statscards:
        card_last_modified = _normalize_last_played(card)
        if card_last_modified is not None:
            if last_played is None or card_last_modified > last_played:
                last_played = card_last_modified
        if card['format'] == 'LongTimespan':
            time_stats.append(card)

    if time_stats:
        playtime = _get_playtime_heuristics(time_stats)

    if playtime and playtime <= 0:
        playtime = 0

    return playtime, last_played
