import deck

import mylogger

logger = mylogger.MAINLOGGER


def export_deck(settings):
    dck = deck.Deck()
    dck.guarded_load(settings.input, settings.readfunc)
    logger.info(verbose_msg=dck)
    dck.guarded_save(settings.output, settings.exportfunc)

