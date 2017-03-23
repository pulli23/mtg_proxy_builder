import deck


def export_deck(settings):
    dck = deck.Deck()
    dck.guarded_load(settings.input, settings.readfunc)
    print(dck)

