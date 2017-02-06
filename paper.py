from typing import Optional, Dict, Tuple


class Paper(object):
    DEFAULTNAMES = {
        "a1paper": (594, 841),
        "a2paper": (420, 594),
        "a3paper": (297, 420),
        "a4paper": (210, 297),
        "letterpaper": (215.9, 279.4)
    }

    def __init__(self, name: Optional[str] = None, width: float = 0, height: float = 0,
                 margins: Optional[Tuple[float, float]] =None):
        self.width = width
        self.height = height
        self.name = name
        if self.name is not None:
            self.width, self.height = self.DEFAULTNAMES[name]
        if margins is None:
            self.margins = (5, 5)
        else:
            self.margins = margins


